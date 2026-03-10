import os
import json

import joblib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.datasets import load_wine
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    ConfusionMatrixDisplay,
)
from fastapi import FastAPI
from pydantic import BaseModel

MODEL_PATH = "wine_model.pkl"
COLUMNS_PATH = "model_columns.json"
METRICS_DIR = "model_metrics"


def _save_confusion_matrix(y_true, y_pred, title, filepath):
    cm = confusion_matrix(y_true, y_pred)
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=["class_0", "class_1", "class_2"])
    disp.plot(cmap="Blues")
    plt.title(title)
    plt.tight_layout()
    plt.savefig(filepath, dpi=150)
    plt.close()


def _compute_scores(y_true, y_pred):
    return {
        "accuracy": round(float(accuracy_score(y_true, y_pred)), 4),
        "precision": round(float(precision_score(y_true, y_pred, average="weighted")), 4),
        "recall": round(float(recall_score(y_true, y_pred, average="weighted")), 4),
        "f1_score": round(float(f1_score(y_true, y_pred, average="weighted")), 4),
    }


def train_and_save():
    os.makedirs(METRICS_DIR, exist_ok=True)

    wine = load_wine(as_frame=True)
    X, y = wine.data, wine.target

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    model = LogisticRegression(max_iter=5000, random_state=42)
    model.fit(X_train, y_train)

    joblib.dump(model, MODEL_PATH)
    with open(COLUMNS_PATH, "w") as f:
        json.dump(list(X_train.columns), f)

    y_train_pred = model.predict(X_train)
    train_scores = _compute_scores(y_train, y_train_pred)
    _save_confusion_matrix(y_train, y_train_pred, "Confusion Matrix – Train", os.path.join(METRICS_DIR, "confusion_matrix_train.png"))

    y_test_pred = model.predict(X_test)
    test_scores = _compute_scores(y_test, y_test_pred)
    _save_confusion_matrix(y_test, y_test_pred, "Confusion Matrix – Test", os.path.join(METRICS_DIR, "confusion_matrix_test.png"))

    scores = {"train": train_scores, "test": test_scores}
    with open(os.path.join(METRICS_DIR, "scores.json"), "w") as f:
        json.dump(scores, f, indent=2)

    print("Training complete.")
    print(f"Train scores: {train_scores}")
    print(f"Test scores:  {test_scores}")

app = FastAPI(title="Wine Classification API")

CLASS_NAMES = ["class_0", "class_1", "class_2"]


class WineInput(BaseModel):
    alcohol: float
    malic_acid: float
    ash: float
    alcalinity_of_ash: float
    magnesium: float
    total_phenols: float
    flavanoids: float
    nonflavanoid_phenols: float
    proanthocyanins: float
    color_intensity: float
    hue: float
    od280_od315_of_diluted_wines: float
    proline: float


@app.on_event("startup")
def startup_event():
    if not os.path.exists(MODEL_PATH):
        train_and_save()


@app.get("/health")
def health():
    return {"status": "healthy", "model_loaded": os.path.exists(MODEL_PATH)}


@app.post("/predict")
def predict(wine: WineInput):
    model = joblib.load(MODEL_PATH)

    with open(COLUMNS_PATH, "r") as f:
        columns = json.load(f)
    X = pd.DataFrame([wine.model_dump()]).reindex(columns=columns, fill_value=0)

    prediction = int(model.predict(X)[0])
    probabilities = model.predict_proba(X)[0].tolist()

    return {
        "predicted_class": prediction,
        "class_name": CLASS_NAMES[prediction],
        "confidence": round(max(probabilities), 4),
        "probabilities": {
            name: round(prob, 4) for name, prob in zip(CLASS_NAMES, probabilities)
        },
    }


if __name__ == "__main__":
    train_and_save()
