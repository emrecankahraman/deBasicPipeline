"""
Kafka'dan gelen Amazon Reviews verisi için Spark schema tanımları
"""
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, LongType

# Kafka'dan gelen review'ların schema'sı
REVIEWS_SCHEMA = StructType([
    StructField("Id", IntegerType(), False),
    StructField("ProductId", StringType(), True),
    StructField("UserId", StringType(), True),
    StructField("ProfileName", StringType(), True),
    StructField("HelpfulnessNumerator", IntegerType(), True),
    StructField("HelpfulnessDenominator", IntegerType(), True),
    StructField("Score", IntegerType(), True),
    StructField("Time", LongType(), True),
    StructField("Summary", StringType(), True),
    StructField("Text", StringType(), True),
])
