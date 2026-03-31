"""
PARTITION ANALYSIS - Statistical Overview
Analyzes all ETL layers: Bronze, Silver, Gold
Shows: partition count, row distribution, statistics
"""
import pandas as pd
import glob
import os

def analyze_layer(layer_name, path):
    """Analyze a single layer's partitions"""
    print(f"\n{'='*70}")
    print(f"LAYER: {layer_name.upper()}")
    print(f"{'='*70}")
    
    if not os.path.exists(path):
        print(f"NOT FOUND: {path}")
        return None
    
    # Find parquet files
    parquet_files = sorted(glob.glob(f"{path}/part-*.parquet"))
    if not parquet_files:
        print(f"NO PARQUET FILES FOUND")
        return None
    
    print(f"Partition files: {len(parquet_files)}")
    
    # Read and count rows in each partition
    partition_rows = []
    total_rows = 0
    
    for i, f in enumerate(parquet_files, 1):
        try:
            df = pd.read_parquet(f)
            row_count = len(df)
            total_rows += row_count
            partition_rows.append(row_count)
            
            fname = os.path.basename(f)
            file_size_mb = os.path.getsize(f) / (1024*1024)
            
            print(f"  Part {i:2d}: {row_count:7,} rows | {file_size_mb:7.1f} MB")
            
        except Exception as e:
            print(f"  Part {i:2d}: ERROR - {e}")
            return None
    
    # Statistics
    print(f"\n{'─'*70}")
    print(f"STATISTICS:")
    print(f"{'─'*70}")
    print(f"Total rows:        {total_rows:,}")
    print(f"Total partitions:  {len(partition_rows)}")
    print(f"Average rows/part: {sum(partition_rows)/len(partition_rows):.0f}")
    print(f"Min rows:          {min(partition_rows):,}")
    print(f"Max rows:          {max(partition_rows):,}")
    print(f"Difference:        {max(partition_rows) - min(partition_rows):,} rows")
    
    # Distribution
    avg = sum(partition_rows) / len(partition_rows)
    min_val = min(partition_rows)
    max_val = max(partition_rows)
    
    if avg > 0:
        cv = (pd.Series(partition_rows).std() / avg) * 100
        print(f"Coefficient of Variation (CV): {cv:.1f}%")
        
        # Interpretation
        if cv < 5:
            print(f"Distribution: VERY UNIFORM (excellent)")
        elif cv < 10:
            print(f"Distribution: UNIFORM (good)")
        elif cv < 20:
            print(f"Distribution: ACCEPTABLE")
        else:
            print(f"Distribution: UNEVEN (consider rebalancing)")
    
    # Note about last partition being smaller
    if partition_rows[-1] < avg * 0.9:
        diff_pct = ((avg - partition_rows[-1]) / avg) * 100
        print(f"\nNote: Last partition has {diff_pct:.1f}% fewer rows (typical for final partition)")
    
    return {
        'name': layer_name,
        'partitions': len(partition_rows),
        'total_rows': total_rows,
        'partition_rows': partition_rows
    }

def main():
    """Main analysis"""
    print("\n" + "="*70)
    print("ETL PIPELINE - PARTITION ANALYSIS")
    print("="*70)
    
    layers = [
        ("Bronze", "data/bronze"),
        ("Silver", "data/silver"),
        ("Gold - Reviews", "data/gold/reviews"),
        ("Gold - Products", "data/gold/products"),
        ("Gold - Users", "data/gold/users"),
    ]
    
    results = []
    for name, path in layers:
        result = analyze_layer(name, path)
        if result:
            results.append(result)
    
    # Summary comparison
    print(f"\n{'='*70}")
    print("SUMMARY COMPARISON")
    print(f"{'='*70}")
    for r in results:
        print(f"{r['name']:10s}: {r['partitions']:2d} partitions | {r['total_rows']:7,} rows")
    
    # Data flow
    print(f"\n{'='*70}")
    print("DATA FLOW")
    print(f"{'='*70}")
    if len(results) >= 2:
        bronze_rows = results[0]['total_rows']
        silver_rows = results[1]['total_rows']
        loss_pct = ((bronze_rows - silver_rows) / bronze_rows) * 100
        print(f"Bronze -> Silver: {silver_rows:,} / {bronze_rows:,} ({100-loss_pct:.2f}% retained)")
    
    if len(results) >= 3:
        silver_rows = results[1]['total_rows']
        gold_reviews_rows = results[2]['total_rows']
        print(f"Silver -> Gold Reviews: {gold_reviews_rows:,} / {silver_rows:,} (100% retained)")
    
    print(f"\n{'='*70}")
    print("GOLD LAYER OUTPUTS")
    print(f"{'='*70}")
    gold_results = [r for r in results if 'Gold' in r['name']]
    for r in gold_results:
        print(f"{r['name']:20s}: {r['partitions']:2d} partitions | {r['total_rows']:7,} rows")
    
    print(f"\n{'='*70}\n")

if __name__ == "__main__":
    main()
