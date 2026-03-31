"""
LOAD EMBEDDINGS TO QDRANT
Uploads embedding data to Qdrant vector database

Process:
1. Load all embedding parquet files
2. Create Qdrant collection
3. Batch upload vectors with metadata
4. Verify collection

Requires:
- data/embeddings/ folder with embeddings_part_*.parquet files
- Qdrant running on localhost:6333
"""

import pandas as pd
import glob
import os
from pathlib import Path
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import warnings

warnings.filterwarnings("ignore")

# Configuration
QDRANT_HOST = "localhost"
QDRANT_PORT = 6333
COLLECTION_NAME = "reviews_embeddings"
VECTOR_SIZE = 384

# Paths
BASE_PATH = Path(__file__).parent.parent
EMBEDDINGS_PATH = BASE_PATH / "data" / "embeddings"

print("\n" + "="*70)
print("LOAD EMBEDDINGS TO QDRANT")
print("="*70)

# Step 1: Connect to Qdrant
print(f"\n[1/4] Connecting to Qdrant ({QDRANT_HOST}:{QDRANT_PORT})...")

try:
    client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
    collections = client.get_collections()
    print(f"  ✅ Connected")
except Exception as e:
    print(f"  ❌ Connection failed: {e}")
    exit(1)

# Step 2: Create collection
print(f"\n[2/4] Creating Qdrant collection: {COLLECTION_NAME}...")

try:
    # Delete if exists
    try:
        client.delete_collection(COLLECTION_NAME)
        print(f"  Deleted existing collection")
    except:
        pass
    
    # Create new
    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(
            size=VECTOR_SIZE,
            distance=Distance.COSINE
        )
    )
    print(f"  ✅ Collection created")
    
except Exception as e:
    print(f"  ❌ Creation failed: {e}")
    exit(1)

# Step 3: Load and upload embeddings
print(f"\n[3/4] Loading and uploading embeddings...")

try:
    # Find embedding files
    embedding_files = sorted(glob.glob(str(EMBEDDINGS_PATH / "embeddings_part_*.parquet")))
    
    if not embedding_files:
        print(f"  ❌ No embedding files found in {EMBEDDINGS_PATH}")
        exit(1)
    
    print(f"  Found {len(embedding_files)} embedding files")
    
    total_uploaded = 0
    point_id = 1
    batch_size = 500
    points_batch = []
    
    # Process each embedding file
    for file_idx, efile in enumerate(embedding_files, 1):
        print(f"\n  File {file_idx}/{len(embedding_files)}: {os.path.basename(efile)}")
        
        # Load file
        df = pd.read_parquet(efile)
        print(f"    Loaded {len(df):,} rows")
        
        # Create points
        for _, row in df.iterrows():
            try:
                point = PointStruct(
                    id=point_id,
                    vector=row['embedding'],
                    payload={
                        "review_id": int(row['review_id']),
                        "product_id": str(row['product_id']),
                        "user_id": str(row['user_id']),
                        "summary": str(row['summary'])[:200],
                        "review_text": str(row['review_text'])[:500],
                        "rating": float(row['rating']),
                        "helpfulness_ratio": float(row['helpfulness_ratio'])
                    }
                )
                
                points_batch.append(point)
                point_id += 1
                total_uploaded += 1
                
                # Batch upload
                if len(points_batch) >= batch_size:
                    client.upsert(
                        collection_name=COLLECTION_NAME,
                        points=points_batch
                    )
                    print(f"    Uploaded {total_uploaded:,} vectors")
                    points_batch = []
                    
            except Exception as e:
                print(f"    ERROR on row: {e}")
                continue
        
    # Final batch
    if points_batch:
        client.upsert(
            collection_name=COLLECTION_NAME,
            points=points_batch
        )
        print(f"    Uploaded {total_uploaded:,} vectors (final batch)")
    
    print(f"\n  ✅ Uploaded {total_uploaded:,} vectors total")
    
except Exception as e:
    print(f"  ❌ Upload failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Step 4: Verify
print(f"\n[4/4] Verifying collection...")

try:
    collection_info = client.get_collection(COLLECTION_NAME)
    vector_count = collection_info.points_count
    
    print(f"  Collection: {COLLECTION_NAME}")
    print(f"  Vectors: {vector_count:,}")
    print(f"  Vector size: {VECTOR_SIZE}")
    print(f"  Distance metric: Cosine")
    
    if vector_count == total_uploaded:
        print(f"\n  ✅ Verification passed")
    else:
        print(f"\n  ⚠️ Mismatch: uploaded {total_uploaded:,} but found {vector_count:,}")
    
except Exception as e:
    print(f"  ❌ Verification failed: {e}")
    exit(1)

print("\n" + "="*70)
print("✅ EMBEDDINGS LOADED TO QDRANT")
print("="*70)
print(f"\nNext step: Run semantic search test")
print(f"  python vector/test_search.py")
print("="*70 + "\n")
