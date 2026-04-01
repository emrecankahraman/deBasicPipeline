"""
FastAPI semantic search service for Qdrant-backed review search.

Endpoints:
- GET /health
- POST /search
"""

from __future__ import annotations

import os
import time
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "reviews")
MODEL_NAME = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
DEVICE = os.getenv("EMBEDDING_DEVICE", "cpu")


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=2, description="Natural language query")
    limit: int = Field(default=5, ge=1, le=20)
    with_payload: bool = True
    min_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)


app = FastAPI(
    title="AI-Ready Review Search API",
    description="Semantic search API powered by SentenceTransformers + Qdrant.",
    version="1.0.0",
)

model: Optional[SentenceTransformer] = None
qdrant_client: Optional[QdrantClient] = None


@app.on_event("startup")
def on_startup() -> None:
    global model, qdrant_client

    qdrant_client = QdrantClient(
        host=QDRANT_HOST,
        port=QDRANT_PORT,
        api_key=QDRANT_API_KEY,
    )

    # Fail fast if collection is missing/unreachable.
    qdrant_client.get_collection(QDRANT_COLLECTION)

    model = SentenceTransformer(MODEL_NAME, device=DEVICE)


@app.get("/health")
def health() -> Dict[str, Any]:
    if model is None or qdrant_client is None:
        raise HTTPException(status_code=503, detail="Service is not ready")

    info = qdrant_client.get_collection(QDRANT_COLLECTION)
    return {
        "status": "ok",
        "collection": QDRANT_COLLECTION,
        "points_count": info.points_count,
        "model": MODEL_NAME,
        "device": DEVICE,
    }


@app.post("/search")
def search_reviews(request: SearchRequest) -> Dict[str, Any]:
    if model is None or qdrant_client is None:
        raise HTTPException(status_code=503, detail="Service is not ready")

    query_text = request.query.strip()
    if not query_text:
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    try:
        query_embedding = model.encode(query_text, convert_to_numpy=True).tolist()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Embedding failed: {exc}") from exc

    start_time = time.time()
    try:
        response = qdrant_client.query_points(
            collection_name=QDRANT_COLLECTION,
            query=query_embedding,
            limit=request.limit,
            with_payload=request.with_payload,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Qdrant query failed: {exc}") from exc
    elapsed_ms = (time.time() - start_time) * 1000

    results = []
    for item in response.points:
        score = float(item.score)
        if request.min_score is not None and score < request.min_score:
            continue

        payload = item.payload or {}
        results.append(
            {
                "vector_id": payload.get("review_id", item.id),
                "score": score,
                "product_id": payload.get("product_id"),
                "user_id": payload.get("user_id"),
                "rating": payload.get("rating"),
                "summary": payload.get("summary"),
                "review_text": payload.get("review_text"),
            }
        )

    return {
        "query": query_text,
        "count": len(results),
        "latency_ms": round(elapsed_ms, 2),
        "results": results,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
