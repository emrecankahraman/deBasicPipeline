from __future__ import annotations

import csv
import json
import time
from pathlib import Path
from typing import Dict, Iterable

from confluent_kafka import Producer

from configs.kafka_config import get_producer_config, get_reviews_topic


RAW_DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "raw" / "Reviews.csv"


def _delivery_report(err, msg) -> None:
    """
    Callback for Kafka to report delivery result.
    """
    if err is not None:
        # Hata durumunda sadece log yazıyoruz; ileride logging'e geçirilebilir.
        print(f"Delivery failed for record {msg.key()}: {err}")
    else:
        # Debug amaçlı; çok gürültülü olursa kapatılabilir.
        # print(f"Record produced to {msg.topic()} partition [{msg.partition()}] at offset {msg.offset()}")
        pass


def read_reviews_csv(path: Path) -> Iterable[Dict[str, str]]:
    """
    Stream-like okuma için CSV satırlarını birer dict olarak yield eder.
    """
    if not path.exists():
        raise FileNotFoundError(f"Raw reviews file not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            yield row


def transform_row_to_message(row: Dict[str, str]) -> Dict[str, str]:
    """
    Amazon Reviews.csv satırını pipeline'da kullanacağımız alan isimlerine map eder.
    """
    return {
        "review_id": row.get("Id"),
        "product_id": row.get("ProductId"),
        "user_id": row.get("UserId"),
        "profile_name": row.get("ProfileName"),
        "helpfulness_numerator": row.get("HelpfulnessNumerator"),
        "helpfulness_denominator": row.get("HelpfulnessDenominator"),
        "rating": row.get("Score"),
        "timestamp": row.get("Time"),
        "summary": row.get("Summary"),
        "review_text": row.get("Text"),
    }


def send_reviews(sleep_seconds: float = 0.1, max_records: int | None = None) -> None:
    """
    Reviews.csv dosyasından kayıtları okuyup Kafka 'reviews' topic'ine gönderir.

    :param sleep_seconds: Her kayıt/batch sonrası bekleme süresi (stream'i simüle etmek için).
    :param max_records: Sadece ilk N kaydı göndermek istersen sınırlama; None ise tamamını gönderir.
    """
    config = get_producer_config()
    topic = get_reviews_topic()
    producer = Producer(config)

    print(f"Using raw data file: {RAW_DATA_PATH}")
    print(f"Producing to topic: {topic}")

    sent_count = 0

    try:
        for row in read_reviews_csv(RAW_DATA_PATH):
            msg = transform_row_to_message(row)
            key = msg["review_id"] or msg["product_id"]

            producer.produce(
                topic=topic,
                key=str(key),
                value=json.dumps(msg).encode("utf-8"),
                callback=_delivery_report,
            )

            sent_count += 1

            # Flush buffer ara ara
            if sent_count % 1000 == 0:
                producer.flush()
                print(f"Sent {sent_count} records so far...")

            if max_records is not None and sent_count >= max_records:
                break

            if sleep_seconds > 0:
                time.sleep(sleep_seconds)

        # Kalan mesajları gönder
        producer.flush()
        print(f"Finished sending {sent_count} records to Kafka topic '{topic}'.")
    finally:
        # Producer objesi GC ile de kapanır ama açıkça bırakmak daha temiz.
        producer.flush()


if __name__ == "__main__":
    # Örnek kullanım:
    # python -m producer.send_reviews_to_kafka
    # veya
    # python producer/send_reviews_to_kafka.py
    send_reviews(sleep_seconds=0.05, max_records=10000)

