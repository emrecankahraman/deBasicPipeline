"""
TEST SEMANTIC SEARCH - Simple version
Test search on Qdrant with test embeddings
"""

from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
import warnings

warnings.filterwarnings("ignore")

# Configuration
QDRANT_HOST = "localhost"
QDRANT_PORT = 6333
COLLECTION_NAME = "reviews_test"

print("\n" + "="*70)
print("TEST SEMANTIC SEARCH")
print("="*70)

# Connect
print("\nConnecting to Qdrant...")

try:
    client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
    info = client.get_collection(COLLECTION_NAME)
    print(f"✅ Connected")
    print(f"   Collection: {COLLECTION_NAME}")
    print(f"   Vectors: {info.points_count:,}")
except Exception as e:
    print(f"❌ Connection failed: {e}")
    exit(1)

# Load model
print("\nLoading embedding model...")

try:
    model = SentenceTransformer("all-MiniLM-L6-v2")
    print(f"✅ Model loaded")
except Exception as e:
    print(f"❌ Failed to load model: {e}")
    exit(1)

# Test queries
print("\n" + "="*70)
print("TEST QUERIES")
print("="*70)

queries = [
    "great coffee excellent taste",
    "broken package damaged arrival",
    "perfect gift highly recommended",
    "waste money quality poor"
]

for query in queries:
    print(f"\n{'─'*70}")
    print(f"Query: \"{query}\"")
    print(f"{'─'*70}\n")
    
    try:
        # Generate embedding
        query_vector = model.encode(query, convert_to_numpy=True).tolist()
        
        # Search using query_points
        search_result = client.query_points(
            collection_name=COLLECTION_NAME,
            query=query_vector,
            limit=3
        )
        results = search_result.points
        
        print(f"Top 3 similar reviews:\n")
        
        for i, hit in enumerate(results, 1):
            payload = hit.payload
            
            print(f"  [{i}] Score: {hit.score:.4f}")
            print(f"      Product: {payload['product_id']}")
            print(f"      Rating: {payload['rating']}/5")
            print(f"      Summary: {payload['summary']}")
            print(f"      Review: {payload['review_text'][:100]}...")
            print()
            
    except Exception as e:
        print(f"❌ Search failed: {e}")
        continue

print("="*70)
print("✅ TEST COMPLETE")
print("="*70 + "\n")
