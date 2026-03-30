"""
Count actual rows in CSV
"""
import pandas as pd

print("\nReading CSV...")
df = pd.read_csv("data/raw/Reviews.csv", nrows=None)

print(f"Total CSV rows: {len(df):,}")
print(f"\nColumns: {df.columns.tolist()}")
print(f"\nNull counts:")
for col in ['Id', 'ProductId', 'UserId', 'review_text', 'summary', 'score', 'Time']:
    if col in df.columns:
        nulls = df[col].isna().sum()
        print(f"  {col}: {nulls:,}")

print(f"\nDtypes:")
print(df.dtypes)

print(f"\nFirst row:")
print(df.iloc[0])
