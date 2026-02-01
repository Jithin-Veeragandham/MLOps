import pandas as pd

df = pd.read_csv('data/CC_GENERAL.csv')
print(f"Original: {len(df)} rows")
df = df.dropna()
print(f"After cleaning: {len(df)} rows")
df.to_csv('data/processed.csv', index=False)