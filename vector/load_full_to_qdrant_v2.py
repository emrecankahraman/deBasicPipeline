"""
LOAD FULL EMBEDDINGS TO QDRANT - FIXED VERSION
Loads all 561K embeddings from data/embeddings_full/ to Qdrant
Handles numpy arrays correctly from parquet files
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

# Configuration
EMBEDDINGS_PATH = Path("data/embeddings_full")
QDRANT_HOST = "localhost"
QDRANT_PORT = 6333
COLLECTION_NAME = "reviews"
BATCH_SIZE = 512
VECTOR_SIZE = 384

print("\n" + "="*70)
print("LOADING EMBEDDINGS TO QDRANT (FIXED)")
print("="*70)

# Connect to Qdrant
print(f"\n[STEP 1] Connecting to Qdrant...")
try:
    client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
    print(f"  ✅ Connected to {QDRANT_HOST}:{QDRANT_PORT}")
    
    # Delete if exists
    try:
        client.delete_collection(COLLECTION_NAME)
        print(f"  ✅ Deleted old collection")
    except:
        pass
    
    # Create collection
    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
    )
    print(f"  ✅ Created collection '{COLLECTION_NAME}'")
    
except Exception as e:
    print(f"  ❌ Failed: {e}")
    exit(1)

# Find embedding files
print(f"\n[STEP 2] Finding embedding files...")
embedding_files = sorted(glob.glob(str(EMBEDDINGS_PATH / "embeddings_part_*.parquet")))
print(f"  Found {len(embedding_files)} files")

if not embedding_files:
    print(f"  ❌ No files found!")
    exit(1)

# Load and upsert
print(f"\n[STEP 3] Loading and upserting...")
print(f"{'─'*70}")

start_time = time.time()
total_vectors = 0
total_files = len(embedding_files)

for file_idx, embedding_file in enumerate(embedding_files, 1):
    fname = os.path.basename(embedding_file)
    print(f"\n[{file_idx:2d}/{total_files}] {fname}")
    
    try:
        # Load
        print(f"  Loading...")
        df = pd.read_parquet(embedding_file)
        print(f"  ✅ Loaded {len(df):,} rows")
        
        # Prepare points
        points = []
        for idx, row in df.iterrows():
            try:
                embedding = row['embedding']
                
                # Convert numpy array to list
                if isinstance(embedding, np.ndarray):
                    embedding = embedding.tolist()
                elif hasattr(embedding, 'tolist'):
                    embedding = embedding.tolist()
                
                # Validate
                if not isinstance(embedding, list):
                    continue
                if len(embedding) != VECTOR_SIZE:
                    continue
                
                # Create point
                point = PointStruct(
                    id=int(row['review_id']),
                    vector=embedding,
                    payload={
                        'review_id': int(row['review_id']),
                        'product_id': int(row['product_id']),
                        'user_id': int(row['user_id']),
                        'summary': str(row['summary']) if pd.notna(row['summary']) else "",
                        'review_text': str(row['review_text']) if pd.notna(row['review_text']) else "",
                        'rating': int(row['rating']) if pd.notna(row['rating']) else 0,
                    }
                )
                points.append(point)
            except Exception as e:
                continue
        
        # Upsert in batches
        print(f"  Upserting {len(points):,} points...")
        for batch_start in range(0, len(points), BATCH_SIZE):
            batch = points[batch_start:batch_start + BATCH_SIZE]
            client.upsert(collection_name=COLLECTION_NAME, points=batch)
        
        print(f"  ✅ Upserted {len(points):,} points")
        total_vectors += len(points)
        
        # Progress
        elapsed = time.time() - start_time
        rate = total_vectors / elapsed
        eta = ((561_519 - total_vectors) / rate) if rate > 0 else 0
        print(f"  Progress: {total_vectors:,} vectors | ETA: {eta/60:.0f}m")
        
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        continue

# Verify
print(f"\n{'─'*70}")
print(f"\n[STEP 4] Verifying...")
collection_info = client.get_collection(COLLECTION_NAME)
print(f"  Collection points: {collection_info.points_count:,}")

# Summary
print(f"\n{'='*70}")
print(f"Total vectors loaded: {total_vectors:,}")
print(f"Total time: {(time.time() - start_time)/60:.1f}m")
print(f"\n✅ DONE!")
print(f"\n[NEXT] python vector/test_search_full.py")
print(f"{'='*70}\n")
