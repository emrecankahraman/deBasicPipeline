"""
LOAD TEST EMBEDDINGS TO QDRANT
Simple, clean upload of 1000 test embeddings

1. Load embeddings_test.parquet
2. Create Qdrant collection
3. Upload vectors
4. Verify
"""

import pandas as pd
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import warnings

warnings.filterwarnings("ignore")

# Configuration
QDRANT_HOST = "localhost"
QDRANT_PORT = 6333
COLLECTION_NAME = "reviews_test"
VECTOR_SIZE = 384

print("\n" + "="*70)
print("LOAD TEST EMBEDDINGS TO QDRANT")
print("="*70)

# Step 1: Load test embeddings
print("\n[1/3] Loading test embeddings...")

try:
    df = pd.read_parquet("data/embeddings_test/embeddings_test.parquet")
    print(f"  ✅ Loaded {len(df):,} rows")
    print(f"     Columns: {df.columns.tolist()}")
except Exception as e:
    print(f"  ❌ Failed to load: {e}")
    exit(1)

# Step 2: Connect to Qdrant and create collection
print("\n[2/3] Setting up Qdrant collection...")

try:
    # Connect
    client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
    print(f"  ✅ Connected to Qdrant")
    
    # Delete existing collection
    try:
        client.delete_collection(COLLECTION_NAME)
        print(f"  Deleted existing collection")
    except:
        pass
    
    # Create new collection
    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(
            size=VECTOR_SIZE,
            distance=Distance.COSINE
        )
    )
    print(f"  ✅ Collection created: {COLLECTION_NAME}")
    
except Exception as e:
    print(f"  ❌ Setup failed: {e}")
    exit(1)

# Step 3: Upload vectors
print("\n[3/3] Uploading vectors...")

try:
    points = []
    
    for idx, row in df.iterrows():
        point = PointStruct(
            id=idx + 1,
            vector=row['embedding'],
            payload={
                "review_id": int(row['review_id']),
                "product_id": str(row['product_id']),
                "user_id": str(row['user_id']),
                "summary": str(row['summary'])[:200],
                "review_text": str(row['review_text'])[:500],
                "rating": float(row['rating'])
            }
        )
        points.append(point)
    
    # Upload all at once
    client.upsert(
        collection_name=COLLECTION_NAME,
        points=points
    )
    
    print(f"  ✅ Uploaded {len(points):,} vectors")
    
except Exception as e:
    print(f"  ❌ Upload failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Verify
print("\n[Verify] Checking collection...")

try:
    collection_info = client.get_collection(COLLECTION_NAME)
    vector_count = collection_info.points_count
    
    print(f"  Collection: {COLLECTION_NAME}")
    print(f"  Total vectors: {vector_count:,}")
    print(f"  Vector size: {VECTOR_SIZE}")
    print(f"  Distance: Cosine")
    
    if vector_count == len(df):
        print(f"\n✅ SUCCESS - All {vector_count:,} vectors loaded!")
    else:
        print(f"\n⚠️ WARNING - Mismatch: loaded {len(df)} but found {vector_count}")
        
except Exception as e:
    print(f"  ❌ Verification failed: {e}")
    exit(1)

print("\n" + "="*70)
print("NEXT: Run semantic search test")
print("  python vector/test_search_simple.py")
print("="*70 + "\n")
