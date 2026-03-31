"""
GOLD LAYER
Silver'dan gelen temiz veriye agregasyon, enrichment ve analytics uygulanır
- Product-level aggregation (avg rating, review count, etc)
- User-level aggregation
- Time-based aggregation
- Feature engineering (vectors için hazırlama)
- Vector DB'ye yazılacak format
"""
from pyspark.sql import SparkSession, Window
from pyspark.sql.functions import (
    col, current_timestamp, avg, count, max, min, desc,
    date_format, from_unixtime, row_number, struct,
    collect_list, concat_ws
)


def create_spark_session(app_name="GoldLayer"):
    """Spark session oluştur"""
    return (
        SparkSession.builder
        .appName(app_name)
        .getOrCreate()
    )


def read_silver_batch(spark, silver_path="data/silver"):
    """
    Silver katmanından batch olarak veri oku
    
    Args:
        spark: SparkSession
        silver_path: Silver parquet path'i
        
    Returns:
        DataFrame: Silver katmanı verisi
    """
    silver_df = spark.read.parquet(silver_path)
    
    # Eğer data yoksa, schema'yı manuel olarak belirt
    if silver_df.count() == 0:
        print("⚠️  Silver data boş, schema manuel belirtiliyor")
        schema = """
            Id INT,
            ProductId STRING,
            UserId STRING,
            profile_name STRING,
            helpfulness_numerator INT,
            helpfulness_denominator INT,
            rating INT,
            timestamp LONG,
            summary STRING,
            review_text STRING,
            helpfulness_ratio DOUBLE,
            review_text_length INT,
            processed_at TIMESTAMP,
            transformed_at TIMESTAMP
        """
        silver_df = spark.read.schema(schema).parquet(silver_path)
    
    return silver_df


def process_gold_layer(silver_df):
    """
    Gold katmanı işleme:
    1. Review veri hazırla (vectorization için uygun format)
    2. Product aggregation (istatistikler)
    3. User aggregation (istatistikler)
    4. Datetime parsing ve formatting
    
    Args:
        silver_df: Silver katmanı DataFrame'i
        
    Returns:
        Tuple: (review_df, product_agg_df, user_agg_df)
    """
    
    # Review data - Vector DB'ye yazılacak format
    # Gerekli: id, review_text, summary, metadata
    review_gold_df = silver_df.select(
        col("Id").alias("review_id"),
        col("ProductId").alias("product_id"),
        col("UserId").alias("user_id"),
        col("profile_name"),
        col("summary"),
        col("review_text"),
        col("rating"),
        col("helpfulness_ratio"),
        col("review_text_length"),
        from_unixtime(col("timestamp")).alias("review_date"),
        col("timestamp").alias("review_timestamp"),
        current_timestamp().alias("indexed_at"),
    )
    
    # Product level aggregation
    # Her product için: avg rating, review sayısı, helpful reviews, etc    
    product_gold_df = (
        review_gold_df.select(
            col("product_id"),
            col("rating"),
            col("helpfulness_ratio"),
            col("review_id"),
        )
        .groupBy("product_id")
        .agg(
            count("review_id").alias("total_reviews"),
            avg("rating").alias("avg_rating"),
            min("rating").alias("min_rating"),
            max("rating").alias("max_rating"),
            avg("helpfulness_ratio").alias("avg_helpfulness"),
        )
        .withColumn("aggregated_at", current_timestamp())
    )
    
    # User level aggregation
    # Her user için: review sayısı, avg rating verdiği, etc
    user_gold_df = (
        review_gold_df.select(
            col("user_id"),
            col("rating"),
            col("helpfulness_ratio"),
            col("review_id"),
        )
        .groupBy("user_id")
        .agg(
            count("review_id").alias("total_reviews_given"),
            avg("rating").alias("avg_rating_given"),
            avg("helpfulness_ratio").alias("avg_helpfulness_given"),
        )
        .withColumn("aggregated_at", current_timestamp())
    )
    
    return review_gold_df, product_gold_df, user_gold_df


def write_gold_batch(dataframes_dict, output_paths_dict):
    """
    Gold katmanı DataFrames'ı Parquet'e yaz (batch mode)
    
    Args:
        dataframes_dict: {'reviews': df, 'products': df, 'users': df}
        output_paths_dict: {'reviews': path, 'products': path, 'users': path}
    """
    for name, df in dataframes_dict.items():
        path = output_paths_dict[name]
        print(f"💾 {name} yazılıyor: {path}")
        df.write.mode("overwrite").parquet(path)


def main():
    """Main - Gold layer batch job"""
    print("🟢 GOLD LAYER başlıyor...")
    
    spark = create_spark_session("GoldLayer")
    
    # Silver'dan oku
    silver_df = read_silver_batch(spark)
    print(f"\n📊 Silver'dan {silver_df.count()} satır okundu")
    
    # Gold işleme
    review_df, product_df, user_df = process_gold_layer(silver_df)
    
    # Schema'yı göster
    print("\n=== REVIEW GOLD SCHEMA (Vector DB için) ===")
    review_df.printSchema()
    
    print("\n=== PRODUCT AGGREGATION SCHEMA ===")
    product_df.printSchema()
    
    print("\n=== USER AGGREGATION SCHEMA ===")
    user_df.printSchema()
    
    # Gold DataFrames'ları yaz
    dataframes = {
        'reviews': review_df,
        'products': product_df,
        'users': user_df
    }
    
    output_paths = {
        'reviews': 'data/gold/reviews',
        'products': 'data/gold/products',
        'users': 'data/gold/users'
    }
    
    print("\n✅ Gold katmanı yazılıyor...")
    write_gold_batch(dataframes, output_paths)
    
    print("✅ Gold layer tamamlandı!")
    spark.stop()


if __name__ == "__main__":
    main()
