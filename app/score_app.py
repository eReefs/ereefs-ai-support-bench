import streamlit as st
import yaml
from pathlib import Path
from datetime import datetime
import hashlib
import json
import re

REPO_ROOT = Path(__file__).resolve().parents[1]
SPEC_PATH = REPO_ROOT / "benchmarks" / "ereefs.yaml"

# Directory where run JSON files are stored
RUNS_DIR = REPO_ROOT / "results-tests" / "runs"

# Return a list of all run JSON files
def get_run_files():
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    return sorted(RUNS_DIR.glob("*.json"))

criterion_results = []

st.set_page_config(page_title="eReefs Benchmark Scoring", layout="wide")

@st.cache_data
def load_spec():
    with open(SPEC_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def save_run(run, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(run, f, indent=2)

# Load a run JSON file
def load_run(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

spec = load_spec()
items = spec["items"]
item_dict = {it["id"]: it for it in items}

st.title("eReefs AI Benchmark - Manual Scoring (JSON Run Mode)")

st.sidebar.header("Run Management")

# --- Run selection and session state logic ---
run_files = get_run_files()
def parse_run_label(stem):
    # Expecting format: 20250808T221940Z_Model_Provider
    m = re.match(r"(\d{8})T(\d{6})Z?_(.*?)_(.*)", stem)
    if m:
        date, time, model, provider = m.groups()
        dt = f"{date[:4]}-{date[4:6]}-{date[6:]} {time[:2]}:{time[2:4]}:{time[4:]}"
        return f"{model}_{provider} ({dt})"
    return stem
run_labels = [parse_run_label(p.stem) for p in run_files]

if "selected_run" not in st.session_state:
    st.session_state.selected_run = "<New Run>"

selected_run = st.sidebar.selectbox(
    "Resume existing run or start new",
    ["<New Run>"] + run_labels,
    index=(["<New Run>"] + run_labels).index(st.session_state.selected_run) if st.session_state.selected_run in (["<New Run>"] + run_labels) else 0,
    key="run_selectbox"
)

if selected_run == "<New Run>":
    st.sidebar.subheader("New Run Metadata")
    model_name = st.sidebar.text_input("Model name", key="new_model_name", placeholder="e.g. gpt-4.1, claude-3.5-sonnet, llama-3.1-405b")
    provider = st.sidebar.text_input("Provider", key="new_provider", placeholder="e.g. OpenAI, Anthropic, Meta, Local")
    model_version = st.sidebar.text_input("Model version or date", key="new_model_version", placeholder="e.g. 2025-07-15")
    temperature = st.sidebar.text_input("Temperature", key="new_temperature", placeholder="e.g. 0.2")
    evaluator = st.sidebar.text_input("Evaluator", key="new_evaluator", placeholder="Your name or initials")
    # Tools used as checkboxes
    tool_options = ["Browsing", "Thinking", "Tools"]
    tools_used = [tool for tool in tool_options if st.sidebar.checkbox(tool, key=f"tool_{tool}")]
    run_notes = st.sidebar.text_area("Run notes", key="new_run_notes", placeholder="Any context about the run")
    if st.sidebar.button("Start new run"):
        timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        run_id = f"{timestamp}_{model_name or 'unknown'}_{provider or 'unknown'}"
        run = {
            "run_id": run_id,
            "model_name": model_name,
            "provider": provider,
            "model_version": model_version,
            "temperature": temperature,
            "evaluator": evaluator,
            "tools_used": tools_used,
            "utc_timestamp": timestamp,
            "run_notes": run_notes,
            "status": "incomplete",
            "answers": []
        }
        out_path = RUNS_DIR / f"{run_id}.json"
        save_run(run, out_path)
        st.session_state.selected_run = parse_run_label(run_id)
        st.rerun()
    run = None
    run_path = None
else:
    idx = run_labels.index(selected_run)
    run_path = run_files[idx]
    run = load_run(run_path)

if run is not None:
    st.sidebar.markdown(f"**Run ID:** {run['run_id']}")
    st.sidebar.markdown(f"**Model:** {run['model_name']}")
    st.sidebar.markdown(f"**Provider:** {run['provider']}")
    st.sidebar.markdown(f"**Status:** {run['status']}")
    st.sidebar.markdown(f"**Questions complete:** {len(run['answers'])} / {len(items)}")

    # Progress bar
    st.progress(len(run['answers']) / len(items))

    # List of question IDs and completion
    answered_ids = {a['question_id'] for a in run['answers']}
    question_labels = [f"{it['id']} - {it['title']}" + (" ✅" if it['id'] in answered_ids else "") for it in items]
    # Question navigation with session state for auto-advance
    # Use separate keys for widget and navigation state to avoid StreamlitAPIException
    if "question_selectbox" not in st.session_state or not isinstance(st.session_state["question_selectbox"], int):
        st.session_state["question_selectbox"] = 0
    if "question_selectbox_selectbox" not in st.session_state:
        st.session_state["question_selectbox_selectbox"] = question_labels[st.session_state["question_selectbox"]]
    try:
        choice = st.selectbox(
            "Benchmark item",
            question_labels,
            index=int(st.session_state["question_selectbox"]),
            key="question_selectbox_selectbox",
        )
    except Exception:
        st.session_state["question_selectbox"] = 0
        st.session_state["question_selectbox_selectbox"] = question_labels[0]
        choice = st.selectbox(
            "Benchmark item",
            question_labels,
            index=0,
            key="question_selectbox_selectbox",
        )
    # Ensure choice is always a string (selectbox can return int if index is out of sync)
    if isinstance(choice, int):
        # Defensive: fallback to first option if out of range
        if 0 <= choice < len(question_labels):
            choice_str = question_labels[choice]
        else:
            choice_str = question_labels[0]
    else:
        choice_str = choice
    chosen_id = choice_str.split(" - ")[0].replace(" ✅", "")
    item = item_dict[chosen_id]

    # Find existing answer for this question if any
    answer = next((a for a in run['answers'] if a['question_id'] == chosen_id), None)
    model_answer = answer['model_answer'] if answer else ""
    question_notes = answer['question_notes'] if answer else ""
    criterion_scores = {c['id']: c for c in answer['criterion']} if answer else {}

    st.subheader(f'{item["id"]}: {item["title"]}')
    # Prompt with wrapping
    st.markdown(f"**Prompt:**\n{item['prompt']}")

    st.write("Paste the model's answer")
    model_answer = st.text_area("Model answer", value=model_answer, height=220)

    st.write("Scoring")
    rows = []
    total = 0
    criterion_results = []
    for crit in item["rubric"]:
        cid = crit["id"]
        desc = crit["description"]
        pts = crit["points"]
        helptext = crit.get("scoring_note", "")
        default = criterion_scores.get(cid, {}).get("awarded_points", 0)
        notes_default = criterion_scores.get(cid, {}).get("notes", "")
        col1, col2 = st.columns([0.7, 0.3])
        with col1:
            st.markdown(f"**{cid}**: {desc}")
            if helptext:
                st.caption(helptext)
        with col2:
            score = st.number_input(f"Points for {cid} ({min(0, pts)} - {max(pts, 0)})", min_value=min(0, pts), max_value=max(pts, 0), value=default, step=1, key=f"score_{cid}")
        notes = st.text_input(f"Notes for {cid}", value=notes_default, key=f"notes_{cid}")
        total += score
        criterion_results.append({"id": cid, "awarded_points": score, "max_points": pts, "notes": notes})

    max_points = item.get("max_points", sum(max(0, r["points"]) for r in item["rubric"]))
    st.markdown(f"**Subtotal: {total} / {max_points}**")

    # Collapsible notes field
    with st.expander("Add/View Notes for this question", expanded=False):
        question_notes = st.text_area("Notes for this question", value=question_notes, key="question_notes")

    save = st.button("Save answer for this question")

    if save:
        timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        # Remove any previous answer for this question
        run['answers'] = [a for a in run['answers'] if a['question_id'] != chosen_id]
        run['answers'].append({
            "question_id": chosen_id,
            "criterion": criterion_results,
            "model_answer": model_answer,
            "question_notes": question_notes,
            "timestamp": timestamp
        })
        # Update status if all questions answered
        if len(run['answers']) == len(items):
            run['status'] = "complete"
        else:
            run['status'] = "incomplete"
        save_run(run, run_path)
        # Auto-advance to next question
        question_ids = [it['id'] for it in items]
        try:
            next_idx = question_ids.index(chosen_id) + 1
            if next_idx < len(question_ids):
                st.session_state["question_selectbox"] = next_idx
        except Exception:
            pass
        st.success("Saved answer for this question.")
        st.rerun()

st.markdown("---")
st.caption("This app now writes one JSON per run, supports resuming, and includes per-question notes.")
