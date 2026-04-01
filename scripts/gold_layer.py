"""
GOLD LAYER (Spark)

Outputs:
1) Serving table for search:
   - data/gold/reviews
2) Power BI analytics tables:
   - data/gold/analytics/product_summary
   - data/gold/analytics/monthly_review_summary
   - data/gold/analytics/rating_distribution
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col,
    current_timestamp,
    avg,
    count,
    max,
    min,
    date_format,
    from_unixtime,
)


def create_spark_session(app_name="GoldLayer"):
    return SparkSession.builder.appName(app_name).getOrCreate()


def read_silver_batch(spark, silver_path="data/silver"):
    silver_df = spark.read.parquet(silver_path)
    return silver_df


def process_gold_layer(silver_df):
    # Serving table for embeddings + semantic search
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

    # Power BI: product summary
    product_summary_df = (
        review_gold_df.groupBy("product_id")
        .agg(
            count("review_id").alias("total_reviews"),
            avg("rating").alias("avg_rating"),
            min("rating").alias("min_rating"),
            max("rating").alias("max_rating"),
            avg("helpfulness_ratio").alias("avg_helpfulness"),
        )
        .withColumn("aggregated_at", current_timestamp())
    )

    # Power BI: monthly review summary
    monthly_summary_df = (
        review_gold_df.withColumn("year_month", date_format(col("review_date"), "yyyy-MM"))
        .groupBy("year_month")
        .agg(
            count("review_id").alias("review_count"),
            avg("rating").alias("avg_rating"),
            avg("helpfulness_ratio").alias("avg_helpfulness"),
        )
        .withColumn("aggregated_at", current_timestamp())
        .orderBy("year_month")
    )

    # Power BI: rating distribution
    rating_distribution_df = (
        review_gold_df.groupBy("rating")
        .agg(count("review_id").alias("review_count"))
        .withColumn("aggregated_at", current_timestamp())
        .orderBy("rating")
    )

    return review_gold_df, product_summary_df, monthly_summary_df, rating_distribution_df


def write_gold_batch(dataframes_dict, output_paths_dict):
    for name, df in dataframes_dict.items():
        path = output_paths_dict[name]
        print(f"Writing {name}: {path}")
        df.write.mode("overwrite").parquet(path)


def main():
    print("GOLD LAYER starts...")
    spark = create_spark_session("GoldLayer")

    silver_df = read_silver_batch(spark)
    print(f"Silver rows: {silver_df.count()}")

    review_df, product_summary_df, monthly_summary_df, rating_distribution_df = process_gold_layer(
        silver_df
    )

    dataframes = {
        "reviews": review_df,
        "product_summary": product_summary_df,
        "monthly_review_summary": monthly_summary_df,
        "rating_distribution": rating_distribution_df,
    }

    output_paths = {
        "reviews": "data/gold/reviews",
        "product_summary": "data/gold/analytics/product_summary",
        "monthly_review_summary": "data/gold/analytics/monthly_review_summary",
        "rating_distribution": "data/gold/analytics/rating_distribution",
    }

    write_gold_batch(dataframes, output_paths)

    print("Gold layer completed.")
    spark.stop()


if __name__ == "__main__":
    main()
