from pyspark.sql import SparkSession

spark = (
    SparkSession.builder
    .appName("InspectReviews")
    .getOrCreate()
)

df = (
    spark.read
    .option("header", True)
    .option("inferSchema", True)
    .csv("data/raw/Reviews.csv")
)

print("=== SCHEMA ===")
df.printSchema()

print("=== COLUMNS ===")
print(df.columns)

print("=== SAMPLE ROWS ===")
df.show(5, truncate=False)

spark.stop()