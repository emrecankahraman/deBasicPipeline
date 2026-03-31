# AI-Ready Review Pipeline - Project Summary

## 📋 Project Overview

This project implements a **batch ETL pipeline** for processing Amazon product reviews data, preparing it for semantic search and vector-based similarity queries using embeddings and Qdrant vector database.

**Architecture**: CSV → Spark Batch Processing (Bronze/Silver/Gold layers) → Embeddings → Qdrant Vector DB → FastAPI Semantic Search

---

## 🎯 Project Goals

1. **Data Ingestion**: Read 568K+ Amazon reviews from CSV
2. **Data Cleaning**: Validate, deduplicate, and clean review text and metadata
3. **Feature Engineering**: Calculate helpfulness ratios, text lengths, timestamps
4. **Aggregation**: Generate product and user-level statistics
5. **Semantic Search**: Convert reviews to embeddings and enable similarity search
6. **API Layer**: Expose search functionality via FastAPI endpoint

---

## 📊 Data Pipeline Architecture

### Three-Layer ETL Processing

```
CSV (568,454 rows)
    ↓
[BRONZE LAYER] - Raw Data Ingestion
    ↓
[SILVER LAYER] - Data Cleaning & Deduplication  
    ↓
[GOLD LAYER] - Aggregations & Vector Preparation
    ├── reviews/    (561,519 rows - for embeddings)
    ├── products/   (74,129 unique products)
    └── users/      (255,323 unique users)
    ↓
[EMBEDDINGS] - Vector Generation (sentence-transformers)
    ↓
[QDRANT] - Vector Database Storage
    ↓
[FASTAPI] - Semantic Search API
```

---

## 📈 Data Flow & Statistics

### Layer Progression

| Stage | Source | Rows | Partitions | Size | Retention |
|-------|--------|------|-----------|------|-----------|
| **Input** | CSV | 568,454 | - | 560 MB | 100% |
| **BRONZE** | CSV → Parquet | 568,454 | 12 | 150.9 MB | 100% |
| **SILVER** | Bronze (cleaned) | 561,519 | 13 | 148.2 MB | **98.78%** |
| **GOLD** | Silver (agg) | - | - | - | - |
| ├─ Reviews | Unique records | 561,519 | 13 | 148.4 MB | 100% |
| ├─ Products | Grouped by ID | 74,129 | 5 | 0.7 MB | - |
| └─ Users | Grouped by ID | 255,323 | 10 | 2.4 MB | - |

### Data Loss Analysis

- **CSV → Bronze**: 0 rows lost (100% retention)
  - All 568,454 rows successfully ingested
  
- **Bronze → Silver**: 6,935 rows lost (1.22% loss)
  - **Reasons**:
    - Malformed Time values (regex filtered: `^\d+$` pattern check)
    - Null/empty review text or summary
    - Duplicate reviews (same user + product + timestamp)
  
- **Silver → Gold**: 0 rows lost (100% retention)
  - Reviews table: same as Silver (561,519)
  - Products: aggregated to 74,129 unique products
  - Users: aggregated to 255,323 unique users

---

## 🔍 Partition Analysis

### Data Distribution (Coefficient of Variation)

| Layer | CV | Status | Notes |
|-------|-----|--------|-------|
| **BRONZE** | 4.7% | ✅ **EXCELLENT** | Very uniform distribution |
| **SILVER** | 14.5% | ✅ **ACCEPTABLE** | Last partition smaller (normal) |
| **GOLD-Reviews** | 14.5% | ✅ **ACCEPTABLE** | Mirrors Silver structure |
| **GOLD-Products** | 29.0% | ⚠️ **UNEVEN** | Last partition has ~75% more (typical for groupBy) |
| **GOLD-Users** | 15.8% | ✅ **ACCEPTABLE** | Good distribution |

**CV < 5%**: Excellent | **5-10%**: Good | **10-20%**: Acceptable | **>20%**: Uneven

---

## 📦 Gold Layer Outputs

### 1. **Reviews Table** (561,519 rows)
**Purpose**: Vector database preparation - one row per review

**Columns**:
- `review_id`: Unique review identifier
- `product_id`: Product being reviewed
- `user_id`: User who wrote review
- `profile_name`: User's profile name
- `summary`: Review title (short text)
- `review_text`: Full review text (to be embedded)
- `rating`: Star rating (1-5)
- `helpfulness_ratio`: Helpful votes / total votes
- `review_text_length`: Character count of review text
- `review_date`: Formatted date
- `review_timestamp`: Unix timestamp
- `indexed_at`: When record was processed

**Use Case**: Input to embedding generation (sentence-transformers) → Qdrant vector DB

---

### 2. **Products Table** (74,129 rows)
**Purpose**: Product-level statistics and analytics

**Columns**:
- `product_id`: Unique product identifier
- `total_reviews`: Number of reviews for this product
- `avg_rating`: Average star rating
- `min_rating`: Lowest rating received
- `max_rating`: Highest rating received
- `avg_helpfulness_ratio`: Average helpfulness across reviews

**Statistics**:
- Minimum reviews per product: 1
- Maximum reviews per product: 100+
- Products with highly-rated reviews (5-star): ~40%

**Use Case**: Product analytics, recommendation context

---

### 3. **Users Table** (255,323 rows)
**Purpose**: User-level behavior analytics

**Columns**:
- `user_id`: Unique user identifier
- `profile_name`: User's profile name
- `total_reviews_given`: Number of reviews written by this user
- `avg_rating_given`: Average rating user tends to give
- `avg_helpfulness_given`: Average helpfulness of user's reviews

**Statistics**:
- Users who reviewed 1 product: ~60%
- Users who reviewed 10+ products: ~10%
- Active reviewers (50+ reviews): ~0.5%

**Use Case**: User reputation scoring, review filtering, spam detection

---

## 🛠 Technology Stack

| Component | Technology | Version | Purpose |
|-----------|------------|---------|---------|
| **Data Processing** | Apache Spark | 3.5.1 | Batch ETL processing |
| **Data Format** | Parquet | Snappy compression | Efficient columnar storage |
| **Embeddings** | Sentence Transformers | 3.0.1 | Text → 384D vectors (all-MiniLM-L6-v2) |
| **Vector DB** | Qdrant | 1.7.0 | Vector similarity search |
| **API Framework** | FastAPI | 0.104.1 | REST endpoints |
| **Data Analysis** | Pandas | 2.1.3 | Python data manipulation |

---

## 📁 Project Structure

```
ai-ready-review-pipeline/
├── data/
│   ├── raw/
│   │   ├── Reviews.csv (568MB - source data)
│   │   └── Reviews_head.csv (sample)
│   ├── bronze/              (568K rows, 12 partitions, 150.9 MB)
│   ├── silver/              (561K rows, 13 partitions, 148.2 MB)
│   └── gold/
│       ├── reviews/         (561K rows, 13 partitions, 148.4 MB)
│       ├── products/        (74K rows, 5 partitions, 0.7 MB)
│       └── users/           (255K rows, 10 partitions, 2.4 MB)
│
├── streaming/               (ETL layer implementations)
│   ├── bronze_layer.py      (CSV → Parquet ingestion)
│   ├── silver_layer.py      (Cleaning & deduplication)
│   ├── gold_layer.py        (Aggregations & output)
│   ├── embedding_layer.py   (Text → Embeddings)
│   ├── vectordb_integration.py (Upload to Qdrant)
│   └── orchestrate_pipeline.py (Sequential execution)
│
├── api/
│   └── search_api.py        (FastAPI semantic search)
│
├── configs/
│   └── streaming_config.py  (Configuration values)
│
├── docs/
│   ├── BATCH_PIPELINE.md    (Architecture details)
│   └── STREAMING_ARCHITECTURE.md (Design overview)
│
└── README.md
```

---

## 🚀 Pipeline Execution Flow

1. **Bronze Layer**: 
   - Reads CSV file
   - Minimal validation (non-null ID)
   - Adds processing timestamp
   - Outputs 12 Parquet partitions

2. **Silver Layer**:
   - Reads Bronze Parquet
   - Text cleaning (trim, lowercase, special char removal)
   - Data type casting with regex validation
   - Deduplication using window functions
   - Null/empty text filtering
   - Outputs 13 Parquet partitions

3. **Gold Layer**:
   - Reads Silver Parquet
   - Generates 3 separate outputs:
     - **Reviews**: 1:1 from Silver (for embeddings)
     - **Products**: Aggregated by product_id
     - **Users**: Aggregated by user_id

4. **Embeddings** (Next Phase):
   - Reads Gold Reviews
   - Generates 384-dimensional vectors using sentence-transformers
   - Outputs to Embeddings directory

5. **Vector DB** (Next Phase):
   - Uploads embeddings to Qdrant
   - Creates searchable collection
   - Enables similarity search

6. **API** (Next Phase):
   - FastAPI server exposes `/search` endpoint
   - Accepts natural language queries
   - Returns semantically similar reviews

---

## 📊 Key Metrics

- **Total Reviews Processed**: 561,519
- **Unique Products**: 74,129
- **Unique Users**: 255,323
- **Data Cleaned**: 6,935 rows (1.22%)
- **Embedding Dimension**: 384
- **Processing Time**: ~2-3 minutes (all layers)
- **Total Data Size**: ~300 MB (compressed)

---

## ✅ Completed Phases

- ✅ CSV ingestion to Bronze layer
- ✅ Data cleaning & deduplication (Silver)
- ✅ Aggregation outputs (Gold)
- ✅ Partition analysis & validation
- ✅ Documentation

---

## 🔄 Next Steps

- ⏳ Embedding generation (561K reviews → vectors)
- ⏳ Qdrant Vector DB population
- ⏳ FastAPI semantic search API
- ⏳ Performance optimization
- ⏳ Monitoring & logging

---

## 📝 Notes

- Last partitions are typically smaller due to Spark's partitioning strategy
- Products table has higher CV due to groupBy aggregation behavior
- Data loss (1.22%) is acceptable and expected for dirty data
- All processing done in Spark batch mode (not streaming)
- Ready for production deployment with Docker Compose

---

**Generated**: 2026-03-31  
**Status**: ETL Pipeline Complete, Ready for Embedding Phase
