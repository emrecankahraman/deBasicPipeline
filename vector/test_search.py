"""
TEST SEMANTIC SEARCH
Simple search test on Qdrant collection

Process:
1. Connect to Qdrant
2. Create query embedding
3. Search similar reviews
4. Display results
"""

from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
import warnings

warnings.filterwarnings("ignore")

# Configuration
QDRANT_HOST = "localhost"
QDRANT_PORT = 6333
COLLECTION_NAME = "reviews_embeddings"

print("\n" + "="*70)
print("SEMANTIC SEARCH TEST")
print("="*70)

# Step 1: Connect to Qdrant
print(f"\n[1/3] Connecting to Qdrant...")

try:
    client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
    collection_info = client.get_collection(COLLECTION_NAME)
    print(f"  ✅ Connected to collection: {COLLECTION_NAME}")
    print(f"     Vectors: {collection_info.points_count:,}")
except Exception as e:
    print(f"  ❌ Connection failed: {e}")
    exit(1)

# Step 2: Load embedding model
print(f"\n[2/3] Loading embedding model...")

try:
    model = SentenceTransformer("all-MiniLM-L6-v2")
    print(f"  ✅ Model loaded (384 dimensions)")
except Exception as e:
    print(f"  ❌ Model loading failed: {e}")
    exit(1)

# Step 3: Run test searches
print(f"\n[3/3] Running test searches...\n")

test_queries = [
    "great product quality",
    "broken on arrival",
    "excellent customer service",
    "waste of money",
    "highly recommended"
]

for query in test_queries:
    print(f"{'─'*70}")
    print(f"Query: \"{query}\"")
    print(f"{'─'*70}")
    
    try:
        # Generate query embedding
        query_vector = model.encode(query, convert_to_numpy=True).tolist()
        
        # Search
        results = client.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_vector,
            limit=5,
            score_threshold=0.0
        )
        
        print(f"Found {len(results)} similar reviews:\n")
        
        for i, hit in enumerate(results, 1):
            payload = hit.payload
            score = hit.score
            
            print(f"  {i}. Score: {score:.4f}")
            print(f"     Product: {payload['product_id']}")
            print(f"     Rating: {payload['rating']}/5 ⭐")
            print(f"     Summary: {payload['summary']}")
            print(f"     Review: {payload['review_text'][:150]}...")
            print()
        
    except Exception as e:
        print(f"  ❌ Search failed: {e}")
        continue

print("="*70)
print("✅ SEARCH TEST COMPLETE")
print("="*70)
print("\nNext step: Deploy full API")
print("  python api/search_api.py")
print("="*70 + "\n")
