
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / "results" / "runs"
OUT_CSV = ROOT / "results" / "all_results.csv"
OUT_XLSX = ROOT / "results" / "all_results.xlsx"

files = sorted(RUNS.glob("*.csv"))
if not files:
    print("No run files found.")
    exit(0)

dfs = [pd.read_csv(p) for p in files]
all_df = pd.concat(dfs, ignore_index=True)

# Order columns
cols = ["benchmark_id", "criterion", "description", "awarded_points", "max_points",
        "model_name", "provider", "model_version", "temperature", "evaluator",
        "utc_timestamp", "subtotal", "max_points", "run_notes", "answer_hash"]
# Deduplicate any duplicate 'max_points' column names from list
cols = list(dict.fromkeys(cols))

ordered = [c for c in cols if c in all_df.columns] + [c for c in all_df.columns if c not in cols]
all_df = all_df[ordered]

OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
all_df.to_csv(OUT_CSV, index=False)
with pd.ExcelWriter(OUT_XLSX) as writer:
    all_df.to_excel(writer, sheet_name="results", index=False)

print(f"Wrote {OUT_CSV}")
print(f"Wrote {OUT_XLSX}")
