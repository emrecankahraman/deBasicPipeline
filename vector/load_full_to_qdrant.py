"""
LOAD FULL EMBEDDINGS TO QDRANT
Loads all 561K embeddings from data/embeddings_full/ to Qdrant vector database
"""

import pandas as pd
import numpy as np
import glob
import os
from pathlib import Path
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance
import time
import warnings

warnings.filterwarnings("ignore")

EMBEDDINGS_PATH = Path("data/embeddings_full")
QDRANT_HOST = "localhost"
QDRANT_PORT = 6333
COLLECTION_NAME = "reviews"
BATCH_SIZE = 512
VECTOR_SIZE = 384

print("\n" + "="*70)
print("LOADING EMBEDDINGS TO QDRANT")
print("="*70)

# Step 1: Connect
print(f"\n[STEP 1] Connecting to Qdrant...")
try:
    client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
    try:
        client.delete_collection(COLLECTION_NAME)
    except:
        pass
    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
    )
    print(f"  ✅ Connected and collection created")
except Exception as e:
    print(f"  ❌ Failed: {e}")
    exit(1)

# Step 2: Find files
print(f"\n[STEP 2] Finding files...")
embedding_files = sorted(glob.glob(str(EMBEDDINGS_PATH / "embeddings_part_*.parquet")))
print(f"  Found {len(embedding_files)} files")

if not embedding_files:
    print(f"  ❌ No files!")
    exit(1)

# Step 3: Load and upsert
print(f"\n[STEP 3] Loading and upserting...")
print(f"{'─'*70}")

start_time = time.time()
total_vectors = 0
stats = {'completed': 0, 'failed': 0}

def create_point(row):
    """Create PointStruct from row"""
    try:
        embedding = row['embedding']
        if isinstance(embedding, np.ndarray):
            embedding = embedding.tolist()
        
        return PointStruct(
            id=int(row['review_id']),
            vector=embedding,
            payload={
                'review_id': int(row['review_id']),
                'product_id': str(row['product_id']),
                'user_id': str(row['user_id']),
                'summary': str(row['summary']) if pd.notna(row['summary']) else "",
                'review_text': str(row['review_text']) if pd.notna(row['review_text']) else "",
                'rating': int(row['rating']) if pd.notna(row['rating']) else 0,
            }
        )
    except Exception as e:
        return None

for file_idx, embedding_file in enumerate(embedding_files, 1):
    fname = os.path.basename(embedding_file)
    print(f"\nFile {file_idx}/{len(embedding_files)}: {fname}")
    
    try:
        print(f"  Loading...")
        df = pd.read_parquet(embedding_file)
        print(f"  ✅ Loaded {len(df):,} rows")
        
        # Create points
        print(f"  Creating points...")
        points = []
        for _, row in df.iterrows():
            point = create_point(row)
            if point:
                points.append(point)
        
        print(f"  ✅ Created {len(points):,} points")
        
        # Upsert
        if points:
            for batch_start in range(0, len(points), BATCH_SIZE):
                batch = points[batch_start:batch_start + BATCH_SIZE]
                client.upsert(collection_name=COLLECTION_NAME, points=batch)
            total_vectors += len(points)
        
        stats['completed'] += 1
        
        # Progress
        elapsed = time.time() - start_time
        rate = total_vectors / elapsed if elapsed > 0 else 0
        eta = ((561_519 - total_vectors) / rate) if rate > 0 else 0
        print(f"  Progress: {total_vectors:,}/561,519 | ETA: {eta/60:.0f}m")
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        stats['failed'] += 1
        continue

# Step 4: Verify
print(f"\n{'─'*70}")
collection_info = client.get_collection(COLLECTION_NAME)

# Summary
total_time = time.time() - start_time
print(f"\n{'='*70}")
print(f"Files completed:     {stats['completed']}/{len(embedding_files)}")
print(f"Failed:              {stats['failed']}")
print(f"Total vectors:       {collection_info.points_count:,}")
print(f"Total time:          {total_time/60:.1f}m")

if collection_info.points_count > 0:
    print(f"\n✅ ALL EMBEDDINGS LOADED SUCCESSFULLY!")
    print(f"\n[NEXT] python vector/test_search_full.py")
else:
    print(f"\n⚠️  WARNING: No vectors loaded!")

print(f"{'='*70}\n")
