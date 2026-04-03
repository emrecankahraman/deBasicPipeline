"""
SILVER LAYER
Bronze'dan gelen veriye veri temizliği ve transformasyonu uygulanır
- Null değerler doldurulur veya silinir
- Text temizliği (trim, special chars)
- Duplicate kontrol
- ML/AI için uygun hale getirilir
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, current_timestamp, trim, lower, regexp_replace,
    when, coalesce, row_number, length, desc, lit, isnan, isnull,
    regexp_extract
)
from pyspark.sql.window import Window


def create_spark_session(app_name="SilverLayer"):
    """Spark session oluştur"""
    return (
        SparkSession.builder
        .appName(app_name)
        .getOrCreate()
    )


def read_bronze_batch(spark, bronze_path="data/bronze"):
    """
    Bronze katmanından batch olarak veri oku
    
    Args:
        spark: SparkSession
        bronze_path: Bronze parquet path'i
        
    Returns:
        DataFrame: Bronze katmanı verisi
    """
    bronze_df = spark.read.parquet(bronze_path)
    return bronze_df


def clean_text(text_col):
    """
    Text temizliği:
    - Başı ve sonundaki boşlukları sil
    - Küçük harfe çevir
    - Extra boşlukları tek boşluğa çevir
    - Kontrol karakterlerini sil
    
    Args:
        text_col: Temizlenecek metin kolonu
        
    Returns:
        Column: Temizlenmiş metin
    """
    cleaned = trim(text_col)
    cleaned = lower(cleaned)
    cleaned = regexp_replace(cleaned, r"\s+", " ")  # Multiple spaces -> single space
    cleaned = regexp_replace(cleaned, r"[^\w\s\-.,!?'\"@]", "")  # Special chars sil
    
    return cleaned


def process_silver_layer(bronze_df):
    """
    Silver katmanı işleme:
    1. Text temizliği (Summary, Text)
    2. Null değerler - default değer ata
    3. Helpfulness ratio hesapla
    4. Review length hesapla
    5. Duplicate'leri kaldır (aynı user + aynı product + aynı time)
    6. ML için gereksiz null'ları filtrele
    
    Args:
        bronze_df: Bronze katmanı DataFrame'i
        
    Returns:
        DataFrame: Silver katmanı hazır veri
    """
    silver_df = bronze_df.select(
        col("Id"),
        col("ProductId"),
        col("UserId"),
        col("ProfileName").alias("profile_name"),
        col("HelpfulnessNumerator").alias("helpfulness_numerator"),
        col("HelpfulnessDenominator").alias("helpfulness_denominator"),
        col("Score").alias("rating"),
        col("Time").alias("timestamp"),
        clean_text(col("Summary")).alias("summary"),
        clean_text(col("Text")).alias("review_text"),
        col("processed_at"),
    )
    
    # Helpfulness ratio hesapla (0-1 arası, null ise 0) numerator / denominator 5 kişi faydalı dedi / 10 kişi gördü = 0.5
    #
    silver_df = silver_df.withColumn(
        "helpfulness_ratio",
        when(
            (col("helpfulness_denominator").isNotNull()) & (col("helpfulness_denominator") > 0),
            col("helpfulness_numerator").cast("double") / col("helpfulness_denominator").cast("double")
        ).otherwise(0.0)
    )
    
    # Review text uzunluğu
    silver_df = silver_df.withColumn(
        "review_text_length",
        length(col("review_text"))
    )
    
    # Null profil adını doldur
    silver_df = silver_df.withColumn(
        "profile_name",
        coalesce(col("profile_name"), lit("Unknown"))
    )
    
    # Duplicate'leri kaldır (aynı user + product + time)
    window_spec = Window.partitionBy("UserId", "ProductId", "timestamp").orderBy(desc("processed_at"))
    silver_df = silver_df.withColumn("row_num", row_number().over(window_spec))
    silver_df = silver_df.filter(col("row_num") == 1).drop("row_num")
    
    # ML için gerekli: summary ve review_text boş olamaz
    silver_df = silver_df.filter(
        (col("summary").isNotNull()) & 
        (col("review_text").isNotNull()) &
        (col("summary") != "") &
        (col("review_text") != "")
    )
    
    # Transformation timestamp'i ekle
    silver_df = silver_df.withColumn("transformed_at", current_timestamp())
    
    return silver_df


def write_silver_batch(silver_df, output_path="data/silver"):
    """
    Silver katmanını Parquet'e yaz (batch mode)
    
    Args:
        silver_df: Silver katmanı DataFrame'i
        output_path: Yazılacak path
    """
    silver_df.write.mode("overwrite").parquet(output_path)


def main():
    """Main - Silver layer batch job"""
    print(" SILVER LAYER başlıyor...")
    
    spark = create_spark_session("SilverLayer")
    
    # Bronze'dan oku
    bronze_df = read_bronze_batch(spark)
    
    # Önce schema'yı kontrol et
    print("\n=== BRONZE SCHEMA ===")
    bronze_df.printSchema()
    
    # Filter: numeric değerleri olan satırları bul (regex ile kontrol)
    # Valid: boşluk + rakamlar, Invalid: ' Repeat"""' gibi
    bronze_df = bronze_df.filter(
        (col("HelpfulnessNumerator").rlike("^\\s*-?\\d+$")) |
        (col("HelpfulnessNumerator").isNull())
    )
    bronze_df = bronze_df.filter(
        (col("HelpfulnessDenominator").rlike("^\\s*-?\\d+$")) |
        (col("HelpfulnessDenominator").isNull())
    )
    bronze_df = bronze_df.filter(
        (col("Score").rlike("^\\s*-?\\d+$")) |
        (col("Score").isNull())
    )
    bronze_df = bronze_df.filter(
        (col("Time").rlike("^\\s*-?\\d+$")) |
        (col("Time").isNull())
    )
    
    # Null değerleri sil
    bronze_df = bronze_df.filter(
        (col("HelpfulnessNumerator").isNotNull()) &
        (col("HelpfulnessDenominator").isNotNull()) &
        (col("Score").isNotNull()) &
        (col("Time").isNotNull())
    )
    
    # INT/LONG'e cast et (artık safe)
    bronze_df = bronze_df.withColumn("HelpfulnessNumerator", col("HelpfulnessNumerator").cast("int"))
    bronze_df = bronze_df.withColumn("HelpfulnessDenominator", col("HelpfulnessDenominator").cast("int"))
    bronze_df = bronze_df.withColumn("Score", col("Score").cast("int"))
    bronze_df = bronze_df.withColumn("Time", col("Time").cast("long"))
    
    
    # Silver işleme
    silver_df = process_silver_layer(bronze_df)
    
    # Schema'yı göster
    print("\n=== SILVER SCHEMA ===")
    silver_df.printSchema()
    
    write_silver_batch(silver_df)
    
    print("Silver layer tamamlandı!")
    spark.stop()


if __name__ == "__main__":
    main()
