# Streaming Pipeline Mimarisi (BATCH MODE)

## Veri Akışı

```
CSV (Amazon Reviews)
    ↓
Spark Batch Processing
    ↓
┌─────────────────────────────────────────────────────┐
│         SPARK SQL PROCESSING LAYERS                 │
├─────────────────────────────────────────────────────┤
│                                                     │
│  CSV → [BRONZE] → [SILVER] → [GOLD] → VECTOR DB   │
│                                                     │
│  🟠 Bronze: Ham veri + validation               │
│  🟡 Silver: Temizlenmiş veri + ML hazırlık      │
│  🟢 Gold: Agregasyon + enrichment               │
│                                                     │
└─────────────────────────────────────────────────────┘
```

## Katmanlar Detaylı

### 🟠 BRONZE LAYER (`bronze_layer.py`)
**Amaç:** CSV'den veriyi oku ve olduğu gibi kaydet + minimal validasyon

**İnput:** `data/raw/Reviews.csv`
```
Id,ProductId,UserId,ProfileName,HelpfulnessNumerator,Score,Time,Summary,Text
1,B001E4KFG0,A3SGXH7AUHU8GW,delmartian,1,5,...
```

**Transformasyonlar:**
- CSV'den oku (header + inferSchema)
- Column standardizasyonu
- Null check (Id boş olamaz)
- `processed_at` timestamp ekleme

**Output:** `data/bronze/` (Parquet format)

---

### 🟡 SILVER LAYER (`silver_layer.py`)
**Amaç:** Veri temizliği + ML/AI hazırlık

**Transformasyonlar:**
- **Text Temizliği:** trim, lowercase, special chars kaldırma
- **Null Handling:** ProfileName'ye default ata
- **Feature Engineering:**
  - `helpfulness_ratio` = HelpfulnessNumerator / HelpfulnessDenominator
  - `review_text_length` = metin uzunluğu
- **Deduplication:** Aynı user + product + time kombinasyonu
- **Filtering:** Boş summary/review_text sil

**Output:** `data/silver/` (Parquet)
- Temiz, ML-ready veri
- Vector DB'ye yazılacak format hazırlanmış

---

### 🟢 GOLD LAYER (`gold_layer.py`)
**Amaç:** Agregasyon + enrichment + vector hazırlık

**Çıktılar:**

1. **Reviews (`data/gold/reviews/`)** - Vector DB için
   ```
   review_id, product_id, user_id, profile_name,
   summary, review_text, rating, helpfulness_ratio,
   review_text_length, review_date, indexed_at
   ```

2. **Product Aggregation (`data/gold/products/`)**
   ```
   product_id, total_reviews, avg_rating,
   min_rating, max_rating, avg_helpfulness
   ```

3. **User Aggregation (`data/gold/users/`)**
   ```
   user_id, total_reviews_given,
   avg_rating_given, avg_helpfulness_given
   ```

---

## Çalıştırma

### Seçenek 1: Hepsi Birden (Recommended)
```bash
cd streaming
python orchestrate_pipeline.py
```

### Seçenek 2: Ayrı Ayrı (Debug)
```bash
# Terminal 1
spark-submit streaming/bronze_layer.py

# Terminal 2
spark-submit streaming/silver_layer.py

# Terminal 3
spark-submit streaming/gold_layer.py
```

### Seçenek 3: Manual Spark Submit
```bash
cd streaming
spark-submit --master local[*] bronze_layer.py
spark-submit --master local[*] silver_layer.py
spark-submit --master local[*] gold_layer.py
```

---

## Checkpoint'ler & State Management

Spark Structured Streaming, durabilite için checkpoint'ler kullanır:

```
data/
├── bronze/
│   └── checkpoint/          # Bronze state
├── silver/
│   └── checkpoint/          # Silver state
└── gold/
    ├── checkpoint_reviews/  # Reviews output
    ├── checkpoint_products/ # Products agg
    └── checkpoint_users/    # Users agg
```

**Dikkat:** Checkpoint'ler silinirse stream'i yeniden başlatmanız gerekir!

---

## Veri Şemaları

### Bronze (Raw)
```
Id: INT
ProductId: STRING
UserId: STRING
ProfileName: STRING
HelpfulnessNumerator: INT
HelpfulnessDenominator: INT
Score: INT
Time: LONG (Unix timestamp)
Summary: STRING
Text: STRING
processed_at: TIMESTAMP
```

### Silver (Clean)
```
review_id: INT
product_id: STRING
user_id: STRING
profile_name: STRING
helpfulness_numerator: INT
helpfulness_denominator: INT
rating: INT (Score'dan)
timestamp: LONG
summary: STRING (cleaned)
review_text: STRING (cleaned)
helpfulness_ratio: DOUBLE
review_text_length: INT
processed_at: TIMESTAMP
transformed_at: TIMESTAMP
```

### Gold - Reviews (Vector DB Input)
```
review_id: INT
product_id: STRING
user_id: STRING
profile_name: STRING
summary: STRING
review_text: STRING ← VECTORIZE THIS
rating: INT
helpfulness_ratio: DOUBLE
review_text_length: INT
review_date: STRING
review_timestamp: LONG
indexed_at: TIMESTAMP
```

---

## Ödünü İlerdeki Aşamalara

1. **Embedding Pipeline** → Gold/reviews'ı vektörize et
2. **Vector DB** (Qdrant) → Vektörleri depola
3. **Semantic Search** → Vector benzerliğine göre ara
4. **FastAPI** → HTTP endpoint'i oluştur
5. **Docker Compose** → Hepsi bir arada

---

## Monitoring & Debugging

### Stream Status Kontrol
```bash
# Kafka topic'inde mesajlar var mı?
docker exec kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic reviews \
  --max-messages 5

# Data klasöründe parquet dosyaları var mı?
ls -la data/bronze/
ls -la data/silver/
ls -la data/gold/
```

### Spark UI
Her job başladığında Spark UI açılır: `http://localhost:4040`

### Parquet Dosyaları Oku
```python
spark = SparkSession.builder.appName("Read").getOrCreate()
bronze_df = spark.read.parquet("data/bronze")
bronze_df.show()
```

---

## Configuration

Tüm ayarlar `configs/streaming_config.py`'da:
- Kafka brokers
- Spark settings
- Checkpoint paths
- Vector DB config
- Data quality thresholds
