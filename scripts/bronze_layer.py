"""
BRONZE LAYER
CSV'den gelen ham Amazon Reviews verisi - minimal işlem, olduğu gibi kaydedilir
- CSV'den oku
- Schema validation
- Timestamp ekleme
- Null check
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, current_timestamp


def create_spark_session(app_name="BronzeLayer"):
    """Spark session oluştur"""
    return (
        SparkSession.builder
        .appName(app_name)
        .getOrCreate()
    )


def read_csv_data(spark, csv_path="data/raw/Reviews.csv"):
    """
    CSV'den reviews verisi oku
    
    Args:
        spark: SparkSession
        csv_path: CSV dosyasının path'i
        
    Returns:
        DataFrame: CSV'den okunan veri
    """
    csv_df = (
        spark.read
        .option("header", True)
        .option("inferSchema", True)
        .csv(csv_path)
    )
    
    return csv_df


def process_bronze_layer(csv_df):
    """
    Bronze katmanı işleme:
    1. Column name'lerini normalize et
    2. Timestamp ekle
    3. Null değerleri kontrol et
    
    Args:
        csv_df: CSV'den okunan DataFrame'i
        
    Returns:
        DataFrame: Bronze katmanı hazır veri
    """
    # CSV column'larını standardize et
    bronze_df = csv_df.select(
        col("Id"),
        col("ProductId"),
        col("UserId"),
        col("ProfileName"),
        col("HelpfulnessNumerator"),
        col("HelpfulnessDenominator"),
        col("Score"),
        col("Time"),
        col("Summary"),
        col("Text"),
    )
    
    # Timestamp ekle (processing time)
    bronze_df = bronze_df.withColumn("processed_at", current_timestamp())
    
    # Kontrol: null check (Id boş olamaz)
    bronze_df = bronze_df.filter(col("Id").isNotNull())
    
    return bronze_df


def write_bronze_batch(bronze_df, output_path="data/bronze"):
    """
    Bronze katmanını Parquet'e yaz (batch mode)
    
    Args:
        bronze_df: Bronze katmanı DataFrame'i
        output_path: Yazılacak path
    """
    bronze_df.write.mode("overwrite").parquet(output_path)


def main():
    """Main - Bronze layer batch job"""
    print("BRONZE LAYER başlıyor...")
    
    spark = create_spark_session("BronzeLayer")
    
    # CSV'den oku
    csv_df = read_csv_data(spark)
    
    # Bronze işleme
    bronze_df = process_bronze_layer(csv_df)
    
    # Schema'yı göster
    print("\n=== BRONZE SCHEMA ===")
    bronze_df.printSchema()
    
    write_bronze_batch(bronze_df)
    
    print("Bronze layer tamamlandı!")
    spark.stop()


if __name__ == "__main__":
    main()
