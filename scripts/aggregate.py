

import pandas as pd
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / "results-tests" / "runs"
OUT_CSV = ROOT / "results-tests" / "all_results.csv"
OUT_XLSX = ROOT / "results-tests" / "all_results.xlsx"

files = sorted(RUNS.glob("*.json"))
if not files:
    print("No run files found.")
    exit(0)

rows = []
for f in files:
    with open(f, "r", encoding="utf-8") as fp:
        run = json.load(fp)
    # Only include complete runs
    if run.get("status") != "complete":
        continue
    run_meta = {k: run.get(k, None) for k in [
        "run_id", "model_name", "provider", "model_version", "temperature", "evaluator", "tools_used", "utc_timestamp", "run_notes"
    ]}
    for ans in run.get("answers", []):
        qid = ans.get("question_id")
        model_answer = ans.get("model_answer", "")
        question_notes = ans.get("question_notes", "")
        timestamp = ans.get("timestamp", "")
        for crit in ans.get("criterion", []):
            row = {
                "benchmark_id": qid,
                "criterion": crit.get("id"),
                "awarded_points": crit.get("awarded_points"),
                "max_points": crit.get("max_points"),
                "criterion_notes": crit.get("notes", ""),
                "model_answer": model_answer,
                "question_notes": question_notes,
                "question_timestamp": timestamp,
            }
            row.update(run_meta)
            rows.append(row)

if not rows:
    print("No complete runs found.")
    exit(0)

df = pd.DataFrame(rows)

# Order columns
cols = [
    "benchmark_id", "criterion", "awarded_points", "max_points", "criterion_notes",
    "model_answer", "question_notes", "question_timestamp",
    "model_name", "provider", "model_version", "temperature", "evaluator", "tools_used",
    "utc_timestamp", "run_notes", "run_id"
]
ordered = [c for c in cols if c in df.columns] + [c for c in df.columns if c not in cols]
df = df[ordered]

OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(OUT_CSV, index=False)
with pd.ExcelWriter(OUT_XLSX) as writer:
    df.to_excel(writer, sheet_name="results", index=False)

print(f"Wrote {OUT_CSV}")
print(f"Wrote {OUT_XLSX}")
