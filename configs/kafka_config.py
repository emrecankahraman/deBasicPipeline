from __future__ import annotations

"""
Kafka configuration for the AI-Ready Review Search Pipeline.

Bu modülde, Kafka producer ve consumer için temel ayarlar tutulur.
İlk aşamada lokal bir Kafka kurulumu varsayıyoruz (localhost:9092).
Gerekirse docker-compose ile daha sonra güncellenebilir.
"""

from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class KafkaSettings:
    bootstrap_servers: str = "localhost:9092"
    topic_reviews: str = "reviews"
    security_protocol: str = "PLAINTEXT"

    # Producer tuning
    acks: str = "all"
    linger_ms: int = 5
    batch_num_messages: int = 1000
    enable_idempotence: bool = True


def get_producer_config() -> Dict[str, str]:
    """
    Return confluent-kafka producer configuration dict.
    """
    settings = KafkaSettings()
    return {
        "bootstrap.servers": settings.bootstrap_servers,
        "security.protocol": settings.security_protocol,
        "acks": settings.acks,
        "enable.idempotence": str(settings.enable_idempotence).lower(),
        "linger.ms": str(settings.linger_ms),
        "batch.num.messages": str(settings.batch_num_messages),
    }


def get_reviews_topic() -> str:
    """
    Helper to get the reviews topic name.
    """
    return KafkaSettings().topic_reviews

