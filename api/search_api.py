"""
🌐 SEMANTIC SEARCH API
FastAPI server for semantic search on review embeddings
Powered by Qdrant vector database + sentence-transformers

Endpoints:
  POST /search - Search similar reviews
  GET /health - Health check
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from typing import List, Optional
import uvicorn
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize models
app = FastAPI(
    title="AI-Ready Review Pipeline - Semantic Search",
    description="Search Amazon reviews using semantic similarity",
    version="1.0.0"
)

# Configuration
QDRANT_HOST = "localhost"
QDRANT_PORT = 6333
COLLECTION_NAME = "reviews_collection"
MODEL_NAME = "all-MiniLM-L6-v2"

# Global clients
embedding_model = None
qdrant_client = None

def init_clients():
    """Initialize embedding model and Qdrant client"""
    global embedding_model, qdrant_client
    
    logger.info("Initializing embedding model...")
    embedding_model = SentenceTransformer(MODEL_NAME)
    
    logger.info(f"Connecting to Qdrant ({QDRANT_HOST}:{QDRANT_PORT})...")
    qdrant_client = QdrantClient(
        host=QDRANT_HOST,
        port=QDRANT_PORT
    )
    
    logger.info("✅ Clients initialized")

# Request/Response models
class SearchRequest(BaseModel):
    """Search request"""
    query: str
    limit: int = 10
    threshold: float = 0.0
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "great product quality",
                "limit": 10,
                "threshold": 0.0
            }
        }

class ReviewResult(BaseModel):
    """Single review result"""
    score: float
    review_id: str
    product_id: str
    user_id: str
    summary: str
    review_text: str
    rating: float
    helpfulness: float

class SearchResponse(BaseModel):
    """Search response"""
    query: str
    results: List[ReviewResult]
    total_results: int
    query_time_ms: float

# Startup/Shutdown events
@app.on_event("startup")
async def startup():
    """Initialize on startup"""
    try:
        init_clients()
        logger.info("✅ API started successfully")
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise

@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown"""
    global qdrant_client
    if qdrant_client:
        qdrant_client.close()
        logger.info("Qdrant client closed")

# Health check
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    try:
        if qdrant_client:
            qdrant_client.get_collections()
        return {
            "status": "healthy",
            "service": "semantic-search-api",
            "collection": COLLECTION_NAME
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unavailable")

# Search endpoint
@app.post("/search", response_model=SearchResponse, tags=["Search"])
async def semantic_search(request: SearchRequest):
    """
    Search for similar reviews using semantic similarity
    
    Args:
        query: Search query (e.g., "great product")
        limit: Number of results (default: 10)
        threshold: Minimum similarity score (default: 0.0)
    
    Returns:
        SearchResponse with matching reviews
    """
    import time
    start_time = time.time()
    
    try:
        logger.info(f"🔍 Searching: {request.query}")
        
        # Validate input
        if not request.query or len(request.query.strip()) == 0:
            raise HTTPException(
                status_code=400,
                detail="Query cannot be empty"
            )
        
        if request.limit < 1 or request.limit > 100:
            raise HTTPException(
                status_code=400,
                detail="Limit must be between 1 and 100"
            )
        
        # Generate query embedding
        query_embedding = embedding_model.encode(
            request.query,
            show_progress_bar=False
        ).tolist()
        
        # Search in Qdrant
        search_results = qdrant_client.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_embedding,
            limit=request.limit,
            score_threshold=request.threshold
        )
        
        # Format results
        results = []
        for hit in search_results:
            payload = hit.payload
            results.append(
                ReviewResult(
                    score=hit.score,
                    review_id=payload.get("review_id", "unknown"),
                    product_id=payload.get("product_id", "unknown"),
                    user_id=payload.get("user_id", "unknown"),
                    summary=payload.get("summary", ""),
                    review_text=payload.get("review_text", ""),
                    rating=payload.get("rating", 0.0),
                    helpfulness=payload.get("helpfulness", 0.0)
                )
            )
        
        query_time_ms = (time.time() - start_time) * 1000
        
        logger.info(f"✅ Found {len(results)} results in {query_time_ms:.2f}ms")
        
        return SearchResponse(
            query=request.query,
            results=results,
            total_results=len(results),
            query_time_ms=query_time_ms
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Search error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}"
        )

# Batch search endpoint (optional)
@app.post("/search_batch", tags=["Search"])
async def batch_search(queries: List[str], limit: int = 5):
    """
    Search for multiple queries at once
    
    Args:
        queries: List of search queries
        limit: Number of results per query (default: 5)
    
    Returns:
        List of search responses
    """
    try:
        results = []
        for query in queries:
            response = await semantic_search(
                SearchRequest(query=query, limit=limit)
            )
            results.append(response)
        
        logger.info(f"✅ Batch search completed for {len(queries)} queries")
        
        return {
            "total_queries": len(queries),
            "results": results
        }
    except Exception as e:
        logger.error(f"❌ Batch search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Root endpoint
@app.get("/", tags=["Info"])
async def root():
    """API info"""
    return {
        "service": "AI-Ready Review Pipeline - Semantic Search API",
        "version": "1.0.0",
        "docs": "/docs",
        "openapi": "/openapi.json"
    }

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🌐 SEMANTIC SEARCH API başlıyor...")
    print("="*60)
    print("\n📖 API Documentation: http://localhost:8000/docs\n")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
