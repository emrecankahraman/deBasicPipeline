"""
EMBEDDING LAYER
Converts review_text to vector embeddings using sentence-transformers
Outputs to data/embeddings/ in Parquet format
"""

import glob
import os
import sys
import warnings
from pathlib import Path

import pandas as pd
from sentence_transformers import SentenceTransformer

warnings.filterwarnings("ignore")

# Configure paths
BASE_PATH = Path(__file__).parent.parent
GOLD_REVIEWS_PATH = BASE_PATH / "data" / "gold" / "reviews"
EMBEDDINGS_OUTPUT_PATH = BASE_PATH / "data" / "embeddings"

# Create output directory
os.makedirs(EMBEDDINGS_OUTPUT_PATH, exist_ok=True)


def load_reviews():
    """Load reviews from gold layer parquet output."""
    print(f" Loading reviews from {GOLD_REVIEWS_PATH}...")

    parquet_files = sorted(glob.glob(str(GOLD_REVIEWS_PATH / "*.parquet")))
    if not parquet_files:
        parquet_files = sorted(glob.glob(str(GOLD_REVIEWS_PATH / "part-*.parquet")))

    if not parquet_files:
        raise FileNotFoundError(f"No parquet files found under {GOLD_REVIEWS_PATH}")

    dataframes = [pd.read_parquet(file_path) for file_path in parquet_files]
    reviews_df = pd.concat(dataframes, ignore_index=True)
    print(f" Loaded {len(reviews_df):,} reviews")
    return reviews_df


def create_model(model_name="all-MiniLM-L6-v2"):
    """Load embedding model once."""
    print(f" Loading model: {model_name}...")
    return SentenceTransformer(model_name)


def process_embeddings(reviews_df, model, batch_size=128):
    """Generate embeddings for review_text column."""
    print("\n Generating embeddings...")

    working_df = reviews_df.copy()
    texts = working_df["review_text"].fillna("").astype(str).tolist()

    embeddings = model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=True,
        convert_to_numpy=True,
    )

    working_df["embedding"] = [embedding.tolist() for embedding in embeddings]

    embeddings_df = working_df[
        [
            "review_id",
            "product_id",
            "user_id",
            "summary",
            "review_text",
            "rating",
            "helpfulness_ratio",
            "embedding",
        ]
    ].copy()

    return embeddings_df


def save_embeddings(embeddings_df):
    """Save embeddings to Parquet."""
    print(f"\n Saving embeddings to {EMBEDDINGS_OUTPUT_PATH}...")

    output_file = EMBEDDINGS_OUTPUT_PATH / "part-00000.parquet"
    embeddings_df.to_parquet(output_file, index=False)

    print(" Embeddings saved successfully")
    print(f" Output file: {output_file}")
    print(f" Total vectors: {len(embeddings_df):,}")


def main():
    """Main pipeline."""
    print("\n" + "=" * 60)
    print(" EMBEDDING LAYER başlıyor...")
    print("=" * 60)

    try:
        reviews_df = load_reviews()
        model = create_model()
        embeddings_df = process_embeddings(reviews_df, model)
        save_embeddings(embeddings_df)

        print("\n" + "=" * 60)
        print(" EMBEDDING LAYER başarıyla tamamlandı!")
        print("=" * 60)
        return 0

    except Exception as e:
        print(f"\n  EMBEDDING LAYER hatası: {str(e)}")
        print(f" Error details: {type(e).__name__}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
