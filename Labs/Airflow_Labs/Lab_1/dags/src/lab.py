import pandas as pd
import numpy as np
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
import optuna
import pickle
import os
import base64


def load_data():
    """
    Checks if train/test CSVs exist in ../data/. If not, downloads Iris
    and splits into train/test. Returns base64-encoded serialized train data.
    """
    data_dir = os.path.join(os.path.dirname(__file__), "../data")
    train_path = os.path.join(data_dir, "file.csv")
    test_path = os.path.join(data_dir, "test.csv")

    if os.path.exists(train_path) and os.path.exists(test_path):
        print("Data files found, loading from disk...")
        df_train = pd.read_csv(train_path)
    else:
        print("Data files not found, downloading Iris dataset...")
        os.makedirs(data_dir, exist_ok=True)
        iris = load_iris(as_frame=True)
        df = iris.frame  # columns: sepal length/width, petal length/width, target
        df_train, df_test = train_test_split(df, test_size=0.2, random_state=42, stratify=df["target"])
        df_train.to_csv(train_path, index=False)
        df_test.to_csv(test_path, index=False)
        print(f"Saved train ({len(df_train)}) and test ({len(df_test)}) to {data_dir}")

    serialized_data = pickle.dumps(df_train)
    return base64.b64encode(serialized_data).decode("ascii")


def data_preprocessing(data_b64: str):
    """
    Deserializes base64-encoded pickled data, performs preprocessing,
    and returns base64-encoded pickled feature/target arrays.
    """
    data_bytes = base64.b64decode(data_b64)
    df = pickle.loads(data_bytes)
    df = df.dropna()

    X = df.drop("target", axis=1)
    y = df["target"]

    payload = {"X_train": X.values, "y_train": y.values}
    serialized_data = pickle.dumps(payload)
    return base64.b64encode(serialized_data).decode("ascii")


def build_save_model(data_b64: str, filename: str):
    """
    Uses Optuna to tune RandomForest hyperparameters via cross-validation.
    Saves the best model. Returns trial results (JSON-serializable).
    """
    data_bytes = base64.b64decode(data_b64)
    payload = pickle.loads(data_bytes)

    X_train = payload["X_train"]
    y_train = payload["y_train"]

    def objective(trial):
        params = {
            "n_estimators": trial.suggest_int("n_estimators", 10, 300),
            "max_depth": trial.suggest_int("max_depth", 2, 15),
            "min_samples_split": trial.suggest_int("min_samples_split", 2, 10),
            "min_samples_leaf": trial.suggest_int("min_samples_leaf", 1, 8),
            "max_features": trial.suggest_categorical("max_features", ["sqrt", "log2", None]),
            "random_state": 42,
        }
        rf = RandomForestClassifier(**params)
        # 5-fold cross-validation on training data
        from sklearn.model_selection import cross_val_score
        scores = cross_val_score(rf, X_train, y_train, cv=5, scoring="accuracy")
        return scores.mean()

    study = optuna.create_study(direction="maximize")
    study.optimize(objective, n_trials=50)

    # Retrain best model on full training data and save
    best_rf = RandomForestClassifier(**study.best_params, random_state=42)
    best_rf.fit(X_train, y_train)

    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "model")
    os.makedirs(output_dir, exist_ok=True)
    with open(os.path.join(output_dir, filename), "wb") as f:
        pickle.dump(best_rf, f)

    trials = [
        {"number": t.number, "accuracy": round(t.value, 4), "params": t.params}
        for t in study.trials
    ]
    return trials


def load_model_evaluate(filename: str, trials: list):
    """
    Loads the best saved model, evaluates on test.csv,
    prints and saves classification report. Returns first prediction as int.
    """
    output_path = os.path.join(os.path.dirname(__file__), "../model", filename)
    loaded_model = pickle.load(open(output_path, "rb"))

    # Log best trial
    best = max(trials, key=lambda t: t["accuracy"])
    print(f"Best trial #{best['number']}: CV accuracy={best['accuracy']}")
    print(f"Best params: {best['params']}")

    # Load and preprocess test data (same scaling)
    df_test = pd.read_csv(os.path.join(os.path.dirname(__file__), "../data/test.csv"))
    X_test = df_test.drop("target", axis=1)
    y_test = df_test["target"]

    preds = loaded_model.predict(X_test)

    # Generate and save classification report
    report = classification_report(y_test, preds, target_names=["setosa", "versicolor", "virginica"])
    print(f"\nClassification Report:\n{report}")

    report_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "model")
    report_path = os.path.join(report_dir, "classification_report.txt")
    with open(report_path, "w") as f:
        f.write(report)
    print(f"Report saved to {report_path}")

    pred = preds[0]
    try:
        return int(pred)
    except Exception:
        return pred.item() if hasattr(pred, "item") else pred