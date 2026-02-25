Airflow Lab 1
=============

An Apache Airflow pipeline that trains an Optuna-tuned RandomForest classifier on the Iris dataset. The DAG is defined in `dags/dag.py` and the pipeline logic lives in `src/lab.py`.

Changes from Original Lab
--------------------------
- Swapped credit card dataset with Iris (auto-downloads if missing)
- Replaced KMeans (unsupervised) with RandomForest (supervised)
- Replaced manual k-loop + elbow method with Optuna HPO (50 trials, 5-fold CV, tuning 5 hyperparameters)
- Removed MinMaxScaler (tree-based models don't need feature scaling)
- Added train/test split with stratification
- Final task evaluates on held-out test set and saves a classification report to `model/classification_report.txt`

Pipeline
--------
- **load_data** — Downloads Iris dataset and splits 80/20 (if CSVs don't already exist in `data/`)
- **data_preprocessing** — Drops nulls, separates features and target
- **build_save_model** — Optuna tunes RandomForest across 5 hyperparameters, saves best model
- **load_model_evaluate** — Evaluates on test set, saves classification report to `model/`

Getting Started
---------------

### 1. Clone the repo

```bash
git clone https://github.com/Jithin-Veeragandham/MLOps.git
cd MLOps/Labs/Airflow_Labs/Lab_1
echo -e "AIRFLOW_UID=50000\n" > .env # setup env with airflow uid
```

### 2. Start Airflow 
Make sure Docker desktop is running and then:

```powershell
docker compose up airflow-init
docker compose up
```

Wait until you see:
```
airflow-webserver-1  | 127.0.0.1 - - [...] "GET /health HTTP/1.1" 200 ...
```

### 3. Open the Airflow UI

Go to http://localhost:8080 and log in:
- Username: `airflow2`
- Password: `airflow2`

### 4. Run the pipeline

- Find **Airflow_Lab1** in the DAGs list
- Toggle it **on**, then click **Trigger DAG**
- Monitor progress in the Graph view

### 5. Check outputs

After the DAG completes:
- `model/model.sav` — trained RandomForest model
- `model/classification_report.txt` — evaluation results
- Best hyperparameters are printed in the `load_model_task` logs

### 6. Stop Airflow

```powershell
docker compose down
```

To fully reset (wipe database and start fresh):
```powershell
docker compose down -v
```
