"""
LOAD FULL EMBEDDINGS TO QDRANT - ULTRA FAST
Uses vectorized numpy operations instead of iterrows
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
print("LOADING EMBEDDINGS TO QDRANT - FAST")
print("="*70)

# Connect
print(f"\n[STEP 1] Connecting...")
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
    print(f"  ✅ Ready")
except Exception as e:
    print(f"  ❌ Failed: {e}")
    exit(1)

# Find files
print(f"\n[STEP 2] Finding {len(sorted(glob.glob(str(EMBEDDINGS_PATH / 'embeddings_part_*.parquet'))))} files...")
embedding_files = sorted(glob.glob(str(EMBEDDINGS_PATH / "embeddings_part_*.parquet")))

if not embedding_files:
    print(f"  ❌ No files!")
    exit(1)

# Load and upsert
print(f"\n[STEP 3] Loading and upserting...")
print(f"{'─'*70}")

start_time = time.time()
total_vectors = 0

for file_idx, embedding_file in enumerate(embedding_files, 1):
    fname = os.path.basename(embedding_file)
    print(f"\n[{file_idx:2d}/{len(embedding_files)}] {fname}")
    
    try:
        print(f"  Loading...")
        df = pd.read_parquet(embedding_file)
        print(f"  ✅ {len(df):,} rows")
        
        # Create points using list comprehension (much faster than iterrows)
        print(f"  Creating points...")
        points = []
        for review_id, product_id, user_id, summary, review_text, rating, embedding in zip(
            df['review_id'].astype(int),
            df['product_id'].astype(str),
            df['user_id'].astype(str),
            df['summary'].fillna("").astype(str),
            df['review_text'].fillna("").astype(str),
            df['rating'].astype(int),
            df['embedding']
        ):
            try:
                # Convert numpy array to list
                vec = embedding.tolist() if isinstance(embedding, np.ndarray) else list(embedding)
                if len(vec) == VECTOR_SIZE:
                    points.append(PointStruct(
                        id=review_id,
                        vector=vec,
                        payload={
                            'review_id': review_id,
                            'product_id': product_id,
                            'user_id': user_id,
                            'summary': summary,
                            'review_text': review_text,
                            'rating': rating,
                        }
                    ))
            except:
                pass
        
        print(f"  ✅ Created {len(points):,} points")
        
        # Upsert in batches
        if points:
            for batch_start in range(0, len(points), BATCH_SIZE):
                batch = points[batch_start:batch_start + BATCH_SIZE]
                client.upsert(collection_name=COLLECTION_NAME, points=batch)
            total_vectors += len(points)
        
        # Progress
        elapsed = time.time() - start_time
        rate = total_vectors / elapsed if elapsed > 0 else 0
        eta = ((561_519 - total_vectors) / rate) if rate > 0 else 0
        print(f"  Progress: {total_vectors:,}/561,519 | ETA: {eta/60:.0f}m")
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        continue

# Verify
print(f"\n{'─'*70}")
collection_info = client.get_collection(COLLECTION_NAME)

# Summary
total_time = time.time() - start_time
print(f"\n{'='*70}")
print(f"Vectors loaded: {collection_info.points_count:,}/561,519")
print(f"Total time:     {total_time/60:.1f}m")

if collection_info.points_count > 0:
    print(f"\n✅ SUCCESS!")
    print(f"[NEXT] python vector/test_search_full.py")
else:
    print(f"\n⚠️  No vectors loaded!")

print(f"{'='*70}\n")
