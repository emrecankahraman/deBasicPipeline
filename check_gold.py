"""Quick check - gold reviews data"""
from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("CheckGold").getOrCreate()

print("\n" + "="*60)
print("CHECKING GOLD REVIEWS")
print("="*60)

# Load reviews
reviews = spark.read.parquet("data/gold/reviews")
count = reviews.count()

print(f"\nOK Total rows: {count:,}")
print(f"\nSchema:")
reviews.printSchema()

print(f"\nSample data:")
reviews.show(5, truncate=False)

print(f"\nColumn stats:")
for col_name in reviews.columns:
    null_count = reviews.filter(f"{col_name} IS NULL").count()
    print(f"  {col_name}: {null_count} nulls")

spark.stop()
