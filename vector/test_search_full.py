"""
SEMANTIC SEARCH ON FULL 561K DATASET
Test semantic search on all 561,519 reviews loaded in Qdrant
"""

from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import PointIdsList
import time

QDRANT_HOST = "localhost"
QDRANT_PORT = 6333
COLLECTION_NAME = "reviews"
MODEL_NAME = "all-MiniLM-L6-v2"
DEVICE = "cuda"

print("\n" + "="*70)
print("SEMANTIC SEARCH - FULL DATASET (561K Reviews)")
print("="*70)

# Connect to Qdrant
print(f"\n[STEP 1] Connecting to Qdrant...")
try:
    client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
    collection_info = client.get_collection(COLLECTION_NAME)
    print(f"  ✅ Connected")
    print(f"     Collection: {COLLECTION_NAME}")
    print(f"     Total vectors: {collection_info.points_count:,}")
except Exception as e:
    print(f"  ❌ Failed: {e}")
    exit(1)

# Load model
print(f"\n[STEP 2] Loading embedding model...")
try:
    model = SentenceTransformer(MODEL_NAME, device=DEVICE)
    print(f"  ✅ Loaded on {DEVICE.upper()}")
except Exception as e:
    print(f"  ❌ Failed: {e}")
    exit(1)

# Test queries
test_queries = [
    "excellent quality great product love it",
    "terrible waste of money broken after one week",
    "good value for money worth buying",
    "amazing fast shipping very happy",
    "poor quality does not work",
    "best coffee ever highly recommend",
    "shipping too slow customer service bad",
    "perfect gift beautiful packaging",
    "disappointed with quality damaged on arrival",
    "fantastic product exactly as described",
]

print(f"\n[STEP 3] Running semantic search queries...")
print(f"{'─'*70}")

for query_idx, query in enumerate(test_queries, 1):
    try:
        # Embed query
        query_embedding = model.encode(query, convert_to_numpy=True).tolist()
        
        # Search in Qdrant using query_points
        start = time.time()
        results = client.query_points(
            collection_name=COLLECTION_NAME,
            query=query_embedding,
            limit=5,
            with_payload=True
        )
        elapsed = time.time() - start
        
        print(f"\n[Query {query_idx:2d}] \"{query}\"")
        print(f"  Search time: {elapsed*1000:.1f}ms")
        print(f"  Results:")
        
        for rank, result in enumerate(results.points, 1):
            payload = result.payload
            score = result.score
            
            summary = payload.get('summary', '')[:50]
            rating = payload.get('rating', 0)
            
            print(f"    [{rank}] Score: {score:.4f} | Rating: {rating}★ | {summary}...")
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        continue

# Summary
print(f"\n{'─'*70}")
print(f"\n{'='*70}")
print(f"✅ SEMANTIC SEARCH TEST COMPLETE!")
print(f"\nDataset: {collection_info.points_count:,} reviews")
print(f"Model: {MODEL_NAME} (384-dim)")
print(f"Distance: Cosine")
print(f"\n{'='*70}\n")
