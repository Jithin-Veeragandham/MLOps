"""
Sends 200 requests to the Iris Classifier API, simulating realistic production traffic.
Mix of valid predictions (~95%) and invalid requests (~5%) to generate error logs.
"""

import random
import time

import numpy as np
import requests
from sklearn.datasets import load_iris

API_URL = "http://localhost:8000"
N_REQUESTS = 200
ERROR_RATE = 0.05  # 5% bad requests

data = load_iris()
X = data.data

print(f"Sending {N_REQUESTS} requests to {API_URL}/predict ...\n")

success = 0
errors = 0

for i in range(N_REQUESTS):
    # Inject a bad request every ~20 calls
    if random.random() < ERROR_RATE:
        payload = {
            "sepal_length": -1.0,  # invalid — triggers 422
            "sepal_width": round(random.uniform(2.0, 4.5), 2),
            "petal_length": round(random.uniform(1.0, 6.9), 2),
            "petal_width": round(random.uniform(0.1, 2.5), 2),
        }
    else:
        # Pick a real iris sample and add slight noise for variety
        sample = X[random.randint(0, len(X) - 1)]
        noise = np.random.normal(0, 0.15, 4)
        sample = sample + noise
        payload = {
            "sepal_length": round(float(max(0.1, sample[0])), 2),
            "sepal_width": round(float(max(0.1, sample[1])), 2),
            "petal_length": round(float(max(0.1, sample[2])), 2),
            "petal_width": round(float(max(0.1, sample[3])), 2),
        }

    try:
        resp = requests.post(f"{API_URL}/predict", json=payload, timeout=5)
        if resp.status_code == 200:
            result = resp.json()
            print(f"[{i+1:>3}/{N_REQUESTS}] {result['prediction']:<12} confidence={result['confidence']:.3f}")
            success += 1
        else:
            print(f"[{i+1:>3}/{N_REQUESTS}] ERROR {resp.status_code}: {resp.json().get('detail', '')}")
            errors += 1
    except Exception as e:
        print(f"[{i+1:>3}/{N_REQUESTS}] EXCEPTION: {e}")
        errors += 1

    # Randomised delay to simulate realistic traffic patterns
    time.sleep(random.uniform(0.05, 0.2))

print(f"\nDone. Success: {success} | Errors: {errors}")
