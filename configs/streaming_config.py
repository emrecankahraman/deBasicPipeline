"""
Streaming Pipeline Konfigürasyonları
"""

# KAFKA AYARLARI
KAFKA_BROKERS = "localhost:9092"
KAFKA_TOPIC = "reviews"
KAFKA_GROUP_ID = "review-pipeline"

# SPARK AYARLARI
SPARK_MASTER = "local[*]"  # WSL'de local mode
SPARK_SHUFFLE_PARTITIONS = 4
SPARK_SQL_SHUFFLE_PARTITIONS = 4

# LAYER CHECKPOINT'LERİ
BRONZE_CHECKPOINT = "data/bronze/checkpoint"
SILVER_CHECKPOINT = "data/silver/checkpoint"
GOLD_CHECKPOINT = "data/gold/checkpoint"

# LAYER OUTPUT PATHS
BRONZE_PATH = "data/bronze"
SILVER_PATH = "data/silver"
GOLD_REVIEWS_PATH = "data/gold/reviews"
GOLD_PRODUCTS_PATH = "data/gold/products"
GOLD_USERS_PATH = "data/gold/users"

# STREAMING AYARLARI
TRIGGER_INTERVAL = "30 seconds"  # Her 30 saniyede bir trigger
WATERMARK_DELAY = "10 minutes"  # Late data 10 dakika bekle

# VECTOR DB AYARLARI (Gold -> Vector DB)
QDRANT_HOST = "localhost"
QDRANT_PORT = 6333
QDRANT_COLLECTION = "reviews"
VECTOR_SIZE = 384  # sentence-transformers default

# DATA QA THRESHOLDS
MIN_REVIEW_TEXT_LENGTH = 10  # Çok kısa review'ları filtrele
MAX_REVIEW_TEXT_LENGTH = 5000  # Çok uzun review'ları filtrele
MIN_SUMMARY_LENGTH = 5

# AGGREGATION SETTINGS (Gold Layer)
PRODUCT_MIN_REVIEWS = 5  # Agregasyon için minimum review sayısı
USER_MIN_REVIEWS = 3  # User istatistiği için minimum review sayısı
