# Batch Pipeline Mimarisi (CSV → Bronze → Silver → Gold)

## 📊 Veri Akışı

```
Reviews.csv
    ↓
🟠 BRONZE (CSV → Parquet)
    ↓
🟡 SILVER (Text Cleaning + Features)
    ↓
🟢 GOLD (Aggregations + Vector Ready)
    ↓
Vector DB (Qdrant - ileri aşama)
```

## ⚙️ Mimarisinin Detayları

### 🟠 BRONZE LAYER (`bronze_layer.py`)

**Görev:** CSV'den veriyi oku, minimal validasyon yap

**Input:** `data/raw/Reviews.csv`

**Transformasyonlar:**
- CSV oku (header=True, inferSchema=True)
- Null validation (Id ≠ null)
- Timestamp ekleme

**Output:** `data/bronze/` (Parquet)

**Schema:**
```
Id INT, ProductId STRING, UserId STRING, ProfileName STRING,
HelpfulnessNumerator INT, HelpfulnessDenominator INT,
Score INT, Time LONG, Summary STRING, Text STRING,
processed_at TIMESTAMP
```

---

### 🟡 SILVER LAYER (`silver_layer.py`)

**Görev:** Veri temizliği + ML hazırlık

**Input:** `data/bronze/` (Parquet)

**Transformasyonlar:**
1. **Text Cleaning**
   - trim() - başı/sonu boşluk sil
   - lower() - küçük harfe çevir
   - regexp_replace() - spesial karakterleri sil
   - Multiple spaces → single space

2. **Feature Engineering**
   - `helpfulness_ratio` = numerator / denominator (default: 0.0)
   - `review_text_length` = metin uzunluğu

3. **Data Quality**
   - Null ProfileName → "Unknown"
   - Empty text'leri sil
   - Null Summary/Text'leri sil

4. **Deduplication**
   - Aynı user + product + time kombinasyonları kaldır

**Output:** `data/silver/` (Parquet)

**Schema (Temizlenmiş):**
```
Id INT, ProductId STRING, UserId STRING,
profile_name STRING (normalized),
helpfulness_numerator INT, helpfulness_denominator INT,
rating INT, timestamp LONG,
summary STRING (cleaned), review_text STRING (cleaned),
helpfulness_ratio DOUBLE, review_text_length INT,
processed_at TIMESTAMP, transformed_at TIMESTAMP
```

---

### 🟢 GOLD LAYER (`gold_layer.py`)

**Görev:** Agregasyon + Feature Engineering + Vector DB hazırlık

**Input:** `data/silver/` (Parquet)

**Outputs (3 ayrı dosya):**

#### 1. Reviews (Vector DB Input) - `data/gold/reviews/`
```
review_id INT
product_id STRING
user_id STRING
profile_name STRING
summary STRING
review_text STRING ← EMBEDDING MODELİNE GİRECEK
rating INT
helpfulness_ratio DOUBLE
review_text_length INT
review_date STRING (formatted)
review_timestamp LONG
indexed_at TIMESTAMP
```

#### 2. Product Aggregation - `data/gold/products/`
```
product_id STRING
total_reviews LONG
avg_rating DOUBLE
min_rating INT, max_rating INT
avg_helpfulness DOUBLE
aggregated_at TIMESTAMP
```

#### 3. User Aggregation - `data/gold/users/`
```
user_id STRING
total_reviews_given LONG
avg_rating_given DOUBLE
avg_helpfulness_given DOUBLE
aggregated_at TIMESTAMP
```

---

## 🚀 Çalıştırma Yöntemi

### Seçenek 1: Orchestration (Recommended)
```bash
cd /mnt/c/Users/emrec/ai-ready-review-pipeline
python streaming/orchestrate_pipeline.py
```

### Seçenek 2: Bash Script
```bash
bash run_batch_pipeline.sh
```

### Seçenek 3: Sırasıyla Manual
```bash
cd /mnt/c/Users/emrec/ai-ready-review-pipeline

spark-submit streaming/bronze_layer.py
# Bronze tamamlanana kadar bekle...

spark-submit streaming/silver_layer.py
# Silver tamamlanana kadar bekle...

spark-submit streaming/gold_layer.py
```

---

## 📁 Output Yapısı

```
data/
├── raw/
│   ├── Reviews.csv (560MB+ - tam dataset)
│   └── Reviews_head.csv (küçük test)
├── bronze/
│   ├── part-00000.parquet
│   ├── part-00001.parquet
│   ├── _SUCCESS
│   └── ...
├── silver/
│   ├── part-00000.parquet (temizlenmiş)
│   ├── part-00001.parquet
│   ├── _SUCCESS
│   └── ...
└── gold/
    ├── reviews/
    │   ├── part-00000.parquet (Vector DB input)
    │   └── ...
    ├── products/
    │   ├── part-00000.parquet (aggregations)
    │   └── ...
    └── users/
        ├── part-00000.parquet (aggregations)
        └── ...
```

---

## 🔍 Monitoring & Kontrol

### Parquet Dosyalarını Oku
```bash
# WSL'de Python ile
python << 'EOF'
from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("Check").getOrCreate()

# Bronze satır sayısı
bronze = spark.read.parquet("data/bronze")
print(f"Bronze: {bronze.count()} rows")

# Silver satır sayısı
silver = spark.read.parquet("data/silver")
print(f"Silver: {silver.count()} rows")

# Gold Reviews
reviews = spark.read.parquet("data/gold/reviews")
print(f"Reviews: {reviews.count()} rows")
reviews.select("review_id", "review_text", "rating").show(3, truncate=False)

# Gold Products
products = spark.read.parquet("data/gold/products")
print(f"Products: {products.count()} rows")
products.show(3)

# Gold Users
users = spark.read.parquet("data/gold/users")
print(f"Users: {users.count()} rows")
users.show(3)

spark.stop()
EOF
```

### Spark Shell'de Kontrol
```bash
spark-shell

# Bronze
val bronze = spark.read.parquet("data/bronze")
bronze.count()
bronze.printSchema()

# Silver
val silver = spark.read.parquet("data/silver")
silver.show()

# Gold Reviews
val reviews = spark.read.parquet("data/gold/reviews")
reviews.select("review_text").show()

:quit
```

---

## ⏱️ Beklenen Süreler

Bilgisayara bağlı olarak (tahmini):

| Layer | Input | Beklenen Süre |
|-------|-------|---------------|
| Bronze | 560MB CSV | 2-5 dakika |
| Silver | Bronze (cleaned) | 3-8 dakika |
| Gold | Silver | 2-5 dakika |
| **Toplam** | - | **7-18 dakika** |

---

## 🛠️ Hata Giderme

### Bronze Hataları
```
Error: CSV not found
→ Reviews.csv'nin varlığını kontrol et: data/raw/Reviews.csv
```

### Silver Hataları
```
Error: data/bronze not found
→ Bronze'u çalıştırmazdan önce Silver çalıştırmayın
```

### Genel Hatalar
```
Error: Java/Spark version mismatch
→ Spark 3.5.1 ve JDK 17 kurulu mu kontrol et
→ spark-shell çalışıyor mu test et
```

---

## 📋 Configuration

Ayarlar `configs/streaming_config.py`'da:
- BRONZE_PATH = "data/bronze"
- SILVER_PATH = "data/silver"
- GOLD_REVIEWS_PATH = "data/gold/reviews"
- VECTOR_SIZE = 384 (sentence-transformers)
- MIN_REVIEW_TEXT_LENGTH = 10

---

## 🔄 İleri Aşamalar

1. **Embedding** - `review_text` → 384D vector
2. **Qdrant Vector DB** - Vectorları depolama
3. **Semantic Search** - Vector similarity
4. **FastAPI** - HTTP API
5. **Docker Compose** - Containerization
