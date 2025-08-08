
import streamlit as st
import yaml
import pandas as pd
from pathlib import Path
from datetime import datetime
import hashlib

REPO_ROOT = Path(__file__).resolve().parents[1]
SPEC_PATH = REPO_ROOT / "benchmarks" / "ereefs.yaml"
# RUNS_DIR = REPO_ROOT / "results" / "runs"

# Use this path for dummy testing to keep the real runs directory clean
RUNS_DIR = REPO_ROOT / "results-tests" / "runs"

st.set_page_config(page_title="eReefs Benchmark Scoring", layout="wide")

@st.cache_data
def load_spec():
    with open(SPEC_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def hash_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]

spec = load_spec()
items = spec["items"]

st.title("eReefs AI Benchmark - Manual Scoring")

left, right = st.columns([1, 2])

with left:
    st.subheader("Select item")
    item_ids = [f'{it["id"]} - {it["title"]}' for it in items]
    choice = st.selectbox("Benchmark item", item_ids, index=0)
    chosen_id = choice.split(" - ")[0]
    item = next(it for it in items if it["id"] == chosen_id)

    st.subheader("Run metadata")
    model_name = st.text_input("Model name", placeholder="eg. gpt-4.1, claude-3.5-sonnet, llama-3.1-405b")
    provider = st.text_input("Provider", placeholder="eg. OpenAI, Anthropic, Meta, Local")
    model_version = st.text_input("Model version or date", placeholder="eg. 2025-07-15")
    temperature = st.text_input("Temperature", placeholder="eg. 0.2")
    evaluator = st.text_input("Evaluator", placeholder="Your name or initials")
    run_notes = st.text_area("Notes", placeholder="Any context about the run")

with right:
    st.subheader(f'{item["id"]}: {item["title"]}')
    st.write("**Prompt**")
    st.code(item["prompt"])

    st.write("Paste the model's answer")
    model_answer = st.text_area("Model answer", height=220)

    st.write("Scoring")
    rows = []
    total = 0
    for crit in item["rubric"]:
        cid = crit["id"]
        desc = crit["description"]
        pts = crit["points"]
        is_penalty = crit.get("is_penalty", False)
        helptext = crit.get("scoring_note", "")
        default = 0

        # Allow free numeric entry within bounds
        col1, col2 = st.columns([0.7, 0.3])
        with col1:
            st.markdown(f"**{cid}**: {desc}")
            if helptext:
                st.caption(helptext)
        with col2:
            score = st.number_input(f"Points for {cid} ({min(0, pts)} - {max(pts, 0)})", min_value=min(0, pts), max_value=max(pts, 0), value=default, step=1, key=f"score_{cid}")
        total += score
        rows.append({"criterion": cid, "description": desc, "max_points": pts, "awarded_points": score})
    max_points = item.get("max_points", sum(max(0, r["points"]) for r in item["rubric"]))
    st.markdown(f"**Subtotal: {total} / {max_points}**")

    save = st.button("Save evaluation")

    if save:
        timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        answer_hash = hash_text(model_answer) if model_answer else "noanswer"
        run_id = f'{item["id"]}_{model_name or "unknown"}_{timestamp}_{answer_hash}'
        out_path = RUNS_DIR / f"{run_id}.csv"

        df = pd.DataFrame(rows)
        # Add metadata columns
        for col in ["benchmark_id", "model_name", "provider", "model_version", "temperature", "evaluator", "utc_timestamp", "subtotal", "max_points", "run_notes", "answer_hash"]:
            df[col] = None
        df.loc[:, "benchmark_id"] = item["id"]
        df.loc[:, "model_name"] = model_name
        df.loc[:, "provider"] = provider
        df.loc[:, "model_version"] = model_version
        df.loc[:, "temperature"] = temperature
        df.loc[:, "evaluator"] = evaluator
        df.loc[:, "utc_timestamp"] = timestamp
        df.loc[:, "subtotal"] = total
        df.loc[:, "max_points"] = max_points
        df.loc[:, "run_notes"] = run_notes
        df.loc[:, "answer_hash"] = answer_hash

        out_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(out_path, index=False)

        # Save the raw answer alongside as a txt for traceability
        answer_path = RUNS_DIR / f"{run_id}.answer.txt"
        with open(answer_path, "w", encoding="utf-8") as f:
            f.write(model_answer or "")

        st.success(f"Saved {out_path.name}")

st.markdown("---")
st.caption("This app writes one CSV per evaluation in results/runs to minimise Git merge conflicts.")
