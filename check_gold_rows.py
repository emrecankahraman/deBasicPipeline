"""
Read GOLD parquet and count rows
"""
import pandas as pd
import glob

print("\nReading GOLD reviews parquet...")
parquet_files = glob.glob("data/gold/reviews/part-*.parquet")
print(f"Found {len(parquet_files)} partition files")

# Read all partitions
dfs = []
for i, f in enumerate(sorted(parquet_files)):
    try:
        df_part = pd.read_parquet(f)
        print(f"  {i+1}. {len(df_part):,} rows")
        dfs.append(df_part)
    except Exception as e:
        print(f"  ERROR reading {f}: {e}")
        raise

# Combine
df_gold = pd.concat(dfs, ignore_index=True)
print(f"\nTotal GOLD rows: {len(df_gold):,}")

print(f"\nColumns: {df_gold.columns.tolist()}")
print(f"\nFirst row:")
print(df_gold.iloc[0])

print(f"\nData types:")
print(df_gold.dtypes)
