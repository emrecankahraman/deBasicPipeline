import csv
import json
import time
from kafka import KafkaProducer

TOPIC = "reviews"

producer = KafkaProducer(
    bootstrap_servers="localhost:9092",
    value_serializer=lambda v: json.dumps(v).encode("utf-8")
)

with open("data/raw/Reviews.csv", "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)

    for i, row in enumerate(reader):
        message = {
            "Id": row.get("Id"),
            "ProductId": row.get("ProductId"),
            "UserId": row.get("UserId"),
            "ProfileName": row.get("ProfileName"),
            "HelpfulnessNumerator": row.get("HelpfulnessNumerator"),
            "Score": row.get("Score"),
            "Time": row.get("Time"),
            "Summary": row.get("Summary"),
            "Text": row.get("Text"),
        }

        producer.send(TOPIC, message)
        print(f"Sent row {i+1}")

        time.sleep(0.2)

        if i >= 99:
            break

producer.flush()
print("Done.")