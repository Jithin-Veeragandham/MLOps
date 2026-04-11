import json
import logging
import time
import uuid

import joblib
import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# JSON-line logging to api.log
logging.basicConfig(filename="api.log", level=logging.INFO, format="%(message)s", filemode="a")

app = FastAPI(title="Iris Classifier API")
model = joblib.load("iris_model.pkl")
CLASS_NAMES = ["setosa", "versicolor", "virginica"]


class PredictRequest(BaseModel):
    sepal_length: float
    sepal_width: float
    petal_length: float
    petal_width: float


def log_event(request_id: str, endpoint: str, status_code: int, latency_ms: float, **fields):
    payload = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "request_id": request_id,
        "endpoint": endpoint,
        "status_code": status_code,
        "latency_ms": round(latency_ms, 2),
    }
    payload.update(fields)
    logging.info(json.dumps(payload))


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/predict")
def predict(req: PredictRequest):
    request_id = str(uuid.uuid4())
    start = time.time()

    features = [req.sepal_length, req.sepal_width, req.petal_length, req.petal_width]

    # Validate inputs
    for name, val in zip(["sepal_length", "sepal_width", "petal_length", "petal_width"], features):
        if val <= 0:
            latency_ms = (time.time() - start) * 1000
            log_event(request_id, "/predict", 422, latency_ms, error=f"Invalid value for {name}: {val}")
            raise HTTPException(status_code=422, detail=f"Invalid value for {name}")

    X = np.array([features])
    prediction_class = int(model.predict(X)[0])
    proba = model.predict_proba(X)[0]
    confidence = float(proba[prediction_class])
    latency_ms = (time.time() - start) * 1000

    log_event(
        request_id, "/predict", 200, latency_ms,
        prediction=CLASS_NAMES[prediction_class],
        prediction_class=prediction_class,
        confidence=round(confidence, 4),
        sepal_length=req.sepal_length,
        sepal_width=req.sepal_width,
        petal_length=req.petal_length,
        petal_width=req.petal_width,
        prob_setosa=round(float(proba[0]), 4),
        prob_versicolor=round(float(proba[1]), 4),
        prob_virginica=round(float(proba[2]), 4),
    )

    return {
        "prediction": CLASS_NAMES[prediction_class],
        "prediction_class": prediction_class,
        "confidence": round(confidence, 4),
        "probabilities": {
            name: round(float(p), 4)
            for name, p in zip(CLASS_NAMES, proba)
        },
    }
