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

    # Collection erişilebilir mi kontrol et
    collection_info = qdrant_client.get_collection(QDRANT_COLLECTION)
    print(f"[STARTUP] Connected to Qdrant: {QDRANT_HOST}:{QDRANT_PORT}")
    print(f"[STARTUP] Collection: {QDRANT_COLLECTION}")
    print(f"[STARTUP] Points count: {collection_info.points_count}")

    model = SentenceTransformer(MODEL_NAME, device=DEVICE)
    print(f"[STARTUP] Model loaded: {MODEL_NAME} on {DEVICE}")


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
        "qdrant_host": QDRANT_HOST,
        "qdrant_port": QDRANT_PORT,
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

    try:
        collection_info = qdrant_client.get_collection(QDRANT_COLLECTION)
        count_result = qdrant_client.count(collection_name=QDRANT_COLLECTION)
        print("\n=== SEARCH DEBUG START ===")
        print(f"Query: {query_text}")
        print(f"Collection: {QDRANT_COLLECTION}")
        print(f"Points count (collection info): {collection_info.points_count}")
        print(f"Points count (count api): {count_result.count}")
    except Exception as exc:
        print(f"[DEBUG] Collection info alınamadı: {exc}")

    start_time = time.time()
    try:
        # limit'i biraz yüksek çekiyoruz ki filtre sonrası elimizde yeterli sonuç kalsın
        fetch_limit = max(request.limit * 5, 20)

        response = qdrant_client.query_points(
            collection_name=QDRANT_COLLECTION,
            query=query_embedding,
            limit=fetch_limit,
            with_payload=request.with_payload,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Qdrant query failed: {exc}") from exc
    elapsed_ms = (time.time() - start_time) * 1000

    raw_points = response.points if response and response.points else []
    print(f"Raw hit sayısı: {len(raw_points)}")

    results = []
    seen_texts = set()

    for point in raw_points:
        score = float(point.score)
        payload = point.payload or {}

        print("----- RAW POINT -----")
        print(f"id: {point.id}")
        print(f"score: {score}")
        print(f"payload keys: {list(payload.keys())}")

        if request.min_score is not None and score < request.min_score:
            print(f"skip edildi, score düşük: {score} < {request.min_score}")
            continue

        review_text = (payload.get("review_text") or "").strip()
        summary = (payload.get("summary") or "").strip()

        # 1) Çok kısa / anlamsız review'leri ele
        if len(review_text) < 15:
            print(f"skip edildi, review_text çok kısa: {review_text!r}")
            continue

        if len(review_text.split()) < 3:
            print(f"skip edildi, review_text kelime sayısı az: {review_text!r}")
            continue

        # 2) Aynı review_text tekrar tekrar gelmesin
        normalized_text = " ".join(review_text.lower().split())
        if normalized_text in seen_texts:
            print(f"skip edildi, duplicate review_text: {review_text!r}")
            continue
        seen_texts.add(normalized_text)

        results.append(
            {
                "vector_id": payload.get("review_id", point.id),
                "score": score,
                "product_id": payload.get("product_id"),
                "user_id": payload.get("user_id"),
                "rating": payload.get("rating"),
                "summary": summary,
                "review_text": review_text,
            }
        )

        # 3) Kullanıcının istediği limite ulaştıysak dur
        if len(results) >= request.limit:
            break

    print(f"Final result sayısı: {len(results)}")
    print("=== SEARCH DEBUG END ===\n")

    return {
        "query": query_text,
        "count": len(results),
        "latency_ms": round(elapsed_ms, 2),
        "results": results,
    }
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)