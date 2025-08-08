# eReefs AI Knowledge Benchmark

This repository is a lightweight, Git-based workflow to track how well different AI models know about eReefs over time.

## How it works

1. All questions and rubrics live in `benchmarks/ereefs.yaml`.
2. Run a model, paste the model's answer into the local scoring app, and select scores for each rubric item.
3. Each evaluation is saved as a small CSV under `results/runs/`. This reduces Git merge conflicts when multiple people are working from different machines.
4. Use `scripts/aggregate.py` to combine per-run CSVs into a single table under `results/all_results.csv` and `results/all_results.xlsx`.

## Quick start

1. Create and activate a Python environment.
2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

   1. Create the Conda environment. This step can take 10 min. If you are using Anaconda open the default Anaconda Prompt, change to the 
    ```bash
    cd {path to the ereefs-benchmark} 
    conda env create -f environment.yaml
    ```
2. Activate the environment
    ```bash
    conda activate ereefsbench

3. Launch the scoring app from the repo root:

   ```bash
   streamlit run app/score_app.py
   ```

4. In the app, pick a benchmark item, paste the model output, assign scores, and click Save.
5. Commit and push the new files in `results/runs/`.

## Files and folders

- `benchmarks/ereefs.yaml` - Canonical list of benchmark items and rubrics.
- `app/score_app.py` - Streamlit UI for manual scoring and saving results.
- `results/runs/` - One CSV per evaluation, containing per-criterion scores.
- `results/flat/` - Optional place for per-run intermediate files.
- `scripts/aggregate.py` - Aggregates all run files to a master CSV and Excel workbook.
- `requirements.txt` - Minimal dependencies for the app and scripts.
- `docs/` - Markdown questions suitable for printing or viewing on GitHub.

## Tips

- Use one file per evaluation to avoid merge conflicts. The app does this by default.
- Always set model metadata: model name, provider, version, temperature, and date. This makes comparisons over time reliable.
- If you prefer Excel, run `scripts/aggregate.py` to get `results/all_results.xlsx` after collecting runs.
- If you want a nice static site, add GitHub Pages with MkDocs or Quarto later. The core workflow here works fully offline.

