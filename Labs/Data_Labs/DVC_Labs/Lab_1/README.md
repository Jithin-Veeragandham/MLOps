# DVC Lab 2 - Data Version Control with GCP

## Changes from Original Lab

- **Added preprocessing pipeline** (`dvc.yaml`) that automatically removes NaN rows when data is updated
- **Created `helper.ipynb`** to demonstrate full DVC workflow interactively
- **Demonstrated version control**: modified data → pushed to Git & GCS → reverted to previous version

## Ran the instructions in `helper.ipynb` to show outputs at each  stage

1. Initialize DVC and configure GCS remote
2. Track dataset with `dvc add`
3. Run preprocessing pipeline with `dvc repro`
4. Show pipeline caching (skips if unchanged)
5. Modify data (multiply by 2) and rerun pipeline
6. Push changes to Git and GCS
7. View version history and hash differences
8. Revert to previous data version

## Project Structure

```
Lab_1/
├── data/
│   ├── CC_GENERAL.csv          # Raw dataset
│   └── CC_GENERAL.csv.dvc      # DVC tracking file
├── scripts/
│   └── preprocess.py           # Drops NaN rows
├── dvc.yaml                    # Pipeline definition
├── dvc.lock                   
├── helper.ipynb                # Workflow demo notebook
└── README.md
└── old_README.md               # Original readme for the lab
```

## Setup

```bash
# Create virtual environment
python -m venv dvc_lab
.\dvc_lab\Scripts\Activate.ps1  # Windows

# Install dependencies
pip install dvc[gs] pandas
```

## Configure DVC

```bash
dvc init --subdir
dvc remote add -d myremote gs://<your-bucket-name>
dvc remote modify myremote credentialpath "<path-to-gcp-credentials.json>"
```

## Pipeline

Defined in `dvc.yaml`:
```yaml
stages:
  preprocess:
    cmd: python scripts/preprocess.py
    deps:
      - data/CC_GENERAL.csv
      - scripts/preprocess.py
    outs:
      - data/processed.csv
```

Run with:
```bash
dvc repro
```

## Version Control Workflow

```bash
# After modifying data
dvc add data/CC_GENERAL.csv
dvc repro
git add data/CC_GENERAL.csv.dvc dvc.lock
git commit -m "Update dataset"
git push origin Lab-2--DVC
dvc push
```

## Revert to Previous Version

```bash
git checkout HEAD~1 -- data/CC_GENERAL.csv.dvc
dvc checkout --force
```