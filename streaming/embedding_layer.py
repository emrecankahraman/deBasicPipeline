"""
📊 EMBEDDING LAYER
Converts review_text to vector embeddings using sentence-transformers
Outputs to data/embeddings/ in Parquet format
"""

import os
import sys
from pathlib import Path
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, pandas_udf
import pandas as pd
from sentence_transformers import SentenceTransformer
import warnings

warnings.filterwarnings("ignore")

# Configure paths
BASE_PATH = str(Path(__file__).parent.parent)
GOLD_REVIEWS_PATH = f"{BASE_PATH}/data/gold/reviews"
EMBEDDINGS_OUTPUT_PATH = f"{BASE_PATH}/data/embeddings"

# Create output directory
os.makedirs(EMBEDDINGS_OUTPUT_PATH, exist_ok=True)

def create_spark_session():
    """Create Spark session"""
    return SparkSession.builder \
        .appName("EmbeddingLayer") \
        .config("spark.driver.memory", "8g") \
        .config("spark.sql.shuffle.partitions", "200") \
        .getOrCreate()

def load_reviews():
    """Load reviews from gold layer"""
    spark = SparkSession.getActiveSession()
    print(f"📖 Loading reviews from {GOLD_REVIEWS_PATH}...")
    
    reviews_df = spark.read.parquet(GOLD_REVIEWS_PATH)
    print(f"✅ Loaded {reviews_df.count()} reviews")
    print(f"📋 Columns: {reviews_df.columns}")
    
    return reviews_df

def create_embedding_udf(model_name="all-MiniLM-L6-v2"):
    """
    Create Pandas UDF for embedding generation
    Model: all-MiniLM-L6-v2 (384 dimensions, fast, good quality)
    """
    
    # Load model once
    model = SentenceTransformer(model_name)
    
    @pandas_udf("array<float>")
    def embed_text(texts: pd.Series) -> pd.Series:
        """
        Embed texts using sentence-transformers
        Returns array of floats (embeddings)
        """
        # Handle null values
        texts = texts.fillna("")
        
        # Generate embeddings
        embeddings = model.encode(texts.tolist(), show_progress_bar=False)
        
        # Convert to list of lists
        return pd.Series([embedding.tolist() for embedding in embeddings])
    
    return embed_text

def process_embeddings(reviews_df):
    """
    Generate embeddings for review_text column
    """
    print("\n🔄 Generating embeddings...")
    
    # Get embedding UDF
    embed_udf = create_embedding_udf()
    
    # Generate embeddings
    embeddings_df = reviews_df.withColumn(
        "embedding",
        embed_udf(col("review_text"))
    )
    
    # Keep only necessary columns
    embeddings_df = embeddings_df.select(
        "review_id",
        "product_id", 
        "user_id",
        "summary",
        "review_text",
        "rating",
        "helpfulness_ratio",
        "embedding"
    )
    
    return embeddings_df

def save_embeddings(embeddings_df):
    """Save embeddings to Parquet"""
    print(f"\n💾 Saving embeddings to {EMBEDDINGS_OUTPUT_PATH}...")
    
    embeddings_df.write \
        .mode("overwrite") \
        .parquet(EMBEDDINGS_OUTPUT_PATH)
    
    print(f"✅ Embeddings saved successfully")
    print(f"📊 Total vectors: {embeddings_df.count()}")

def main():
    """Main pipeline"""
    print("\n" + "="*60)
    print("🎯 EMBEDDING LAYER başlıyor...")
    print("="*60)
    
    try:
        spark = create_spark_session()
        
        # Load reviews
        reviews_df = load_reviews()
        
        # Generate embeddings
        embeddings_df = process_embeddings(reviews_df)
        
        # Save embeddings
        save_embeddings(embeddings_df)
        
        print("\n" + "="*60)
        print("✅ 🟢 EMBEDDING LAYER başarıyla tamamlandı!")
        print("="*60)
        
        spark.stop()
        return 0
        
    except Exception as e:
        print(f"\n❌ ❌ EMBEDDING LAYER hatası: {str(e)}")
        print(f"📍 Error details: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
