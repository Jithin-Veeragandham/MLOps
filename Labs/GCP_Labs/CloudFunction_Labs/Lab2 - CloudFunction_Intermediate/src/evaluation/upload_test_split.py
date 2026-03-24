import pandas as pd
from sklearn.model_selection import train_test_split
from google.cloud import storage

df = pd.read_csv('data/data.csv')
_, test = train_test_split(df, test_size=0.2, random_state=42)

client = storage.Client()
bucket = client.bucket('mlops-labs-jithin')
bucket.blob('data/test.csv').upload_from_string(test.to_csv(index=False), content_type='text/csv')
print(f'Uploaded data/test.csv ({len(test)} rows)')
