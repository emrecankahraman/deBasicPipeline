"""
Load embeddings to Qdrant.

Input location:
- data/embeddings/*.parquet
"""

import glob
import os
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance

warnings.filterwarnings("ignore")

BASE_PATH = Path(__file__).resolve().parent.parent
EMBEDDINGS_PATH = BASE_PATH / "data" / "embeddings"
QDRANT_HOST = "localhost"
QDRANT_PORT = 6333
COLLECTION_NAME = "reviews"
BATCH_SIZE = 512
VECTOR_SIZE = 384


def connect_qdrant():
    """Connect to Qdrant and recreate the target collection."""
    print(f"\n[STEP 1] Connecting to Qdrant...")
    client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass

    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
    )
    print("  Connected and collection created")
    return client


def find_embedding_files():
    """Find embedding parquet files created by the embedding layer."""
    print(f"\n[STEP 2] Finding files...")
    print(f"  Input path: {EMBEDDINGS_PATH}")

    patterns = [
        "*.parquet",
        "part-*.parquet",
        "embeddings_part_*.parquet",
    ]

    embedding_files = []
    for pattern in patterns:
        embedding_files.extend(glob.glob(str(EMBEDDINGS_PATH / pattern)))

    embedding_files = sorted(set(embedding_files))
    print(f"  Found {len(embedding_files)} files")

    if not embedding_files:
        raise FileNotFoundError(
            f"No embedding files found in {EMBEDDINGS_PATH}. Run python scripts/embedding_layer.py first."
        )

    return embedding_files

def create_point(row):
    """Create PointStruct from row"""
    try:
        embedding = row["embedding"]
        if isinstance(embedding, np.ndarray):
            embedding = embedding.tolist()
        elif hasattr(embedding, "tolist"):
            embedding = embedding.tolist()

        return PointStruct(
            id=int(row["review_id"]),
            vector=embedding,
            payload={
                "review_id": int(row["review_id"]),
                "product_id": str(row["product_id"]),
                "user_id": str(row["user_id"]),
                "summary": str(row["summary"]) if pd.notna(row["summary"]) else "",
                "review_text": str(row["review_text"]) if pd.notna(row["review_text"]) else "",
                "rating": int(row["rating"]) if pd.notna(row["rating"]) else 0,
            },
        )
    except Exception:
        return None


def main():
    print("\n" + "=" * 70)
    print("LOADING EMBEDDINGS TO QDRANT")
    print("=" * 70)

    try:
        client = connect_qdrant()
        embedding_files = find_embedding_files()
    except Exception as e:
        print(f"  Failed during setup: {e}")
        return 1

    print(f"\n[STEP 3] Loading and upserting...")
    print(f"{'─' * 70}")

    start_time = time.time()
    total_vectors = 0
    stats = {"completed": 0, "failed": 0}

    for file_idx, embedding_file in enumerate(embedding_files, 1):
        fname = os.path.basename(embedding_file)
        print(f"\nFile {file_idx}/{len(embedding_files)}: {fname}")

        try:
            print("  Loading...")
            df = pd.read_parquet(embedding_file)
            print(f"  Loaded {len(df):,} rows")

            print("  Creating points...")
            points = []
            for _, row in df.iterrows():
                point = create_point(row)
                if point:
                    points.append(point)

            print(f"  Created {len(points):,} points")

            if points:
                for batch_start in range(0, len(points), BATCH_SIZE):
                    batch = points[batch_start:batch_start + BATCH_SIZE]
                    client.upsert(collection_name=COLLECTION_NAME, points=batch)
                total_vectors += len(points)

            stats["completed"] += 1
            print(f"  Progress: {total_vectors:,} vectors")

        except Exception as e:
            print(f"  Error: {e}")
            stats["failed"] += 1
            continue

    print(f"\n{'─' * 70}")
    collection_info = client.get_collection(COLLECTION_NAME)
    total_time = time.time() - start_time

    print(f"\n{'=' * 70}")
    print(f"Files completed:     {stats['completed']}/{len(embedding_files)}")
    print(f"Failed:              {stats['failed']}")
    print(f"Total vectors:       {collection_info.points_count:,}")
    print(f"Total time:          {total_time/60:.1f}m")

    if collection_info.points_count > 0:
        print("\nALL EMBEDDINGS LOADED SUCCESSFULLY!")
        print("\n[NEXT STEPS]")
        print("  1. python vector/test_search_full.py")
        print("  2. python api/search_api.py")
        print("  3. Open: http://localhost:8000/docs")
        return 0

    print("\nWARNING: No vectors loaded!")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
