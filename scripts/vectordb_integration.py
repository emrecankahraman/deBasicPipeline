"""
🔍 VECTOR DB INTEGRATION LAYER
Uploads embeddings to Qdrant vector database
Creates collections for semantic search

Collections:
- reviews_collection: Full review embeddings for semantic search
"""

import os
import sys
from pathlib import Path
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, row_number
from pyspark.sql.window import Window
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import warnings

warnings.filterwarnings("ignore")

# Configure paths
BASE_PATH = str(Path(__file__).parent.parent)
EMBEDDINGS_PATH = f"{BASE_PATH}/data/embeddings"
QDRANT_HOST = "localhost"
QDRANT_PORT = 6333
COLLECTION_NAME = "reviews_collection"
VECTOR_SIZE = 384  # all-MiniLM-L6-v2 dimension

def create_spark_session():
    """Create Spark session"""
    return SparkSession.builder \
        .appName("VectorDBIntegration") \
        .config("spark.driver.memory", "8g") \
        .getOrCreate()

def connect_qdrant():
    """Connect to Qdrant instance"""
    print(f"🔗 Connecting to Qdrant ({QDRANT_HOST}:{QDRANT_PORT})...")
    
    try:
        client = QdrantClient(
            host=QDRANT_HOST,
            port=QDRANT_PORT
        )
        info = client.get_collections()
        print(f"✅ Connected to Qdrant")
        return client
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        raise

def create_collection(client):
    """Create Qdrant collection if not exists"""
    print(f"📦 Creating collection: {COLLECTION_NAME}...")
    
    try:
        # Delete if exists
        try:
            client.delete_collection(COLLECTION_NAME)
            print(f"  🗑️  Deleted existing collection")
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
        print(f"✅ Collection '{COLLECTION_NAME}' created")
    except Exception as e:
        print(f"❌ Failed to create collection: {e}")
        raise

def load_embeddings():
    """Load embeddings from Parquet"""
    spark = SparkSession.getActiveSession()
    print(f"📖 Loading embeddings from {EMBEDDINGS_PATH}...")
    
    embeddings_df = spark.read.parquet(EMBEDDINGS_PATH)
    print(f"✅ Loaded {embeddings_df.count()} embeddings")
    
    return embeddings_df

def upload_to_qdrant(embeddings_df, client):
    """Upload embeddings to Qdrant"""
    print(f"\n⬆️  Uploading to Qdrant...")
    
    # Collect embeddings (keep in memory for batching)
    data = embeddings_df.collect()
    total_records = len(data)
    
    points = []
    batch_size = 100
    
    for idx, row in enumerate(data):
        try:
            # Create point
            point_id = int(idx) + 1  # Qdrant point IDs start from 1
            embedding = row.embedding
            
            # Create metadata payload
            payload = {
                "review_id": str(row.review_id) if row.review_id else f"unknown_{idx}",
                "product_id": str(row.product_id) if row.product_id else "unknown",
                "user_id": str(row.user_id) if row.user_id else "unknown",
                "summary": str(row.summary)[:200] if row.summary else "",
                "review_text": str(row.review_text)[:500] if row.review_text else "",
                "rating": float(row.rating) if row.rating else 0.0,
                "helpfulness": float(row.helpfulness_ratio) if row.helpfulness_ratio else 0.0
            }
            
            # Create point struct
            point = PointStruct(
                id=point_id,
                vector=embedding,
                payload=payload
            )
            
            points.append(point)
            
            # Batch upload
            if len(points) >= batch_size or idx == total_records - 1:
                client.upsert(
                    collection_name=COLLECTION_NAME,
                    points=points
                )
                print(f"  ✅ Uploaded {min(idx + 1, total_records)} / {total_records}")
                points = []
                
        except Exception as e:
            print(f"  ⚠️  Error uploading point {idx}: {e}")
            continue
    
    print(f"\n✅ Upload completed!")

def verify_collection(client):
    """Verify collection stats"""
    print(f"\n📊 Collection Stats:")
    
    try:
        collection_info = client.get_collection(COLLECTION_NAME)
        points_count = collection_info.points_count
        print(f"  Total vectors: {points_count}")
        print(f"  Vector size: {VECTOR_SIZE} dimensions")
        print(f"  Distance metric: Cosine similarity")
        return points_count > 0
    except Exception as e:
        print(f"❌ Failed to verify: {e}")
        return False

def test_search(client):
    """Test semantic search"""
    print(f"\n🔍 Testing semantic search...")
    
    try:
        # Get a random point to use for search
        results = client.scroll(
            collection_name=COLLECTION_NAME,
            limit=1
        )
        
        if results[0]:
            test_point = results[0][0]
            test_vector = test_point.vector
            
            # Search similar vectors
            search_results = client.search(
                collection_name=COLLECTION_NAME,
                query_vector=test_vector,
                limit=5
            )
            
            print(f"  ✅ Found {len(search_results)} similar vectors")
            print(f"  Top match score: {search_results[0].score:.4f}")
            
    except Exception as e:
        print(f"  ⚠️  Search test error: {e}")

def main():
    """Main pipeline"""
    print("\n" + "="*60)
    print("🎯 VECTOR DB INTEGRATION başlıyor...")
    print("="*60)
    
    try:
        spark = create_spark_session()
        
        # Connect to Qdrant
        client = connect_qdrant()
        
        # Create collection
        create_collection(client)
        
        # Load embeddings
        embeddings_df = load_embeddings()
        
        # Upload to Qdrant
        upload_to_qdrant(embeddings_df, client)
        
        # Verify
        if verify_collection(client):
            test_search(client)
            
            print("\n" + "="*60)
            print("✅ 🟢 VECTOR DB INTEGRATION başarıyla tamamlandı!")
            print("="*60)
            
            spark.stop()
            return 0
        else:
            raise Exception("Collection verification failed")
        
    except Exception as e:
        print(f"\n❌ ❌ VECTOR DB INTEGRATION hatası: {str(e)}")
        print(f"📍 Error details: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
