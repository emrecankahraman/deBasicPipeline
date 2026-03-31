import pandas as pd
import numpy as np

df = pd.read_parquet('data/embeddings_full/embeddings_part_01.parquet')
print("Columns:", df.columns.tolist())
print("\nFirst row:")
for col in df.columns:
    val = df.iloc[0][col]
    if isinstance(val, np.ndarray):
        print(f"  {col}: ndarray shape {val.shape}, first 5: {val[:5]}")
    else:
        print(f"  {col}: {type(val).__name__} = {val}")
