"""
Check partition files and row counts
"""
import os
import glob

print("\n" + "="*60)
print("PARTITION ANALYSIS")
print("="*60)

paths = {
    "BRONZE": "data/bronze",
    "SILVER": "data/silver",
    "GOLD": "data/gold/reviews"
}

for name, path in paths.items():
    print(f"\n{name}: {path}")
    if not os.path.exists(path):
        print("  NOT FOUND")
        continue
    
    # Count parquet files
    parquet_files = glob.glob(f"{path}/part-*.parquet")
    print(f"  Parquet files: {len(parquet_files)}")
    
    # Get total size
    total_size = 0
    for f in parquet_files:
        total_size += os.path.getsize(f)
    
    size_mb = total_size / (1024*1024)
    print(f"  Total size: {size_mb:.1f} MB")
    
    # List files
    for f in sorted(parquet_files)[:3]:
        fname = os.path.basename(f)
        fsize = os.path.getsize(f) / (1024*1024)
        print(f"    {fname}: {fsize:.1f} MB")
    if len(parquet_files) > 3:
        print(f"    ... and {len(parquet_files)-3} more")

print("\n" + "="*60)
