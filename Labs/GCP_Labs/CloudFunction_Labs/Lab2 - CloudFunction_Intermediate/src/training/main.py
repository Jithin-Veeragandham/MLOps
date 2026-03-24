import base64
import json
from google.cloud import storage, pubsub_v1
import joblib
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from io import StringIO

def train_model(event, context):
    message = json.loads(base64.b64decode(event['data']).decode('utf-8'))
    file_name = message.get('file')

    storage_client = storage.Client()
    bucket = storage_client.bucket('mlops-labs-jithin')
    blob = bucket.blob(file_name)
    data = pd.read_csv(StringIO(blob.download_as_text()))

    X = data.drop('species', axis=1)
    y = data['species']
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    clf = RandomForestClassifier(n_estimators=100)
    clf.fit(X_train, y_train)

    model_path = '/tmp/model.pkl'
    with open(model_path, 'wb') as f:
        joblib.dump(clf, f)

    bucket.blob('model.pkl').upload_from_filename(model_path)
    print('Model trained and saved to GCS')

    # Publish to model-evaluation-trigger
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path('testing-488212', 'model-evaluation-trigger')
    payload = json.dumps({"model_path": "model.pkl"}).encode('utf-8')
    publisher.publish(topic_path, payload)
    print('Published to model-evaluation-trigger')