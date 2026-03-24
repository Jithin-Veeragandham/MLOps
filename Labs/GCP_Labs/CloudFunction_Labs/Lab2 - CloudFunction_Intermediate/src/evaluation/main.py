import base64
import json
import os
from google.cloud import storage
from google.cloud import pubsub_v1
import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score
from io import BytesIO

def evaluate_model(event, context):
    publisher = pubsub_v1.PublisherClient()
    project_id = os.environ["GCP_PROJECT"]

    # Decode the Pub/Sub message
    message = base64.b64decode(event["data"]).decode("utf-8")
    data = json.loads(message)
    model_path = data["model_path"]

    # Load model from GCS using joblib to match train_model
    storage_client = storage.Client()
    bucket = storage_client.bucket(os.environ["BUCKET_NAME"])
    blob = bucket.blob(model_path)
    model = joblib.load(BytesIO(blob.download_as_bytes()))

    # Load test data from GCS
    test_blob = bucket.blob("data/test.csv")
    data = pd.read_csv(BytesIO(test_blob.download_as_bytes()))
    X_test = data.drop('species', axis=1)
    y_test = data['species']

    # Evaluate
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    threshold = float(os.environ.get("ACCURACY_THRESHOLD", 0.8))

    print(f"Model accuracy: {accuracy:.4f} | Threshold: {threshold}")

    if accuracy >= threshold:
        topic_path = publisher.topic_path(project_id, "model-serving-trigger")
        payload = json.dumps({"model_path": model_path, "accuracy": accuracy}).encode("utf-8")
        publisher.publish(topic_path, payload)
        print("Evaluation passed. Published to model-serving-trigger.")

        notify_topic = publisher.topic_path(project_id, "pipeline-notifications")
        notify_payload = json.dumps({
            "status": "SUCCESS",
            "stage": "evaluation",
            "reason": f"Model accuracy {accuracy:.4f} passed threshold {threshold}. Ready for serving."
        }).encode("utf-8")
        publisher.publish(notify_topic, notify_payload)
        print("Published SUCCESS notification to pipeline-notifications.")
    else:
        topic_path = publisher.topic_path(project_id, "pipeline-notifications")
        payload = json.dumps({
            "status": "FAILED",
            "stage": "evaluation",
            "reason": f"Accuracy {accuracy:.4f} below threshold {threshold}"
        }).encode("utf-8")
        publisher.publish(topic_path, payload)
        print("Evaluation failed. Published failure notification.")