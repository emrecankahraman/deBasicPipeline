AI-Ready Review Search Pipeline
================================

Bu proje, ürün yorumlarını uçtan uca işleyip semantic search için hazır hale getiren bir veri/ML pipeline’ıdır.

Yüksek seviye akış:

- Dataset (JSON/CSV) → Kafka Producer
- Kafka Topic (`reviews`) → Spark Structured Streaming
- Bronze katmanı (ham stream çıktısı)
- Silver katmanı (temizlenmiş, analiz/ML için hazır veri)
- Embedding pipeline (sentence-transformers)
- Vector DB (Qdrant)
- Basit semantic search (CLI / ileride FastAPI)

### Klasör yapısı (özet)

- `data/`
  - `raw/` – başlangıç dataset
  - `bronze/` – ham stream çıktısı
  - `silver/` – temizlenmiş veri
  - `sample_queries/` – test sorguları
- `producer/` – Kafka producer script’leri
- `streaming/` – Spark streaming job’ları ve temizlik fonksiyonları
- `embeddings/` – embedding modeli ve batch embedding script’leri
- `vectordb/` – Qdrant koleksiyon ve search yardımcıları
- `api/` – (ileride) FastAPI semantic search servisi
- `notebooks/` – veri keşfi, embedding ve arama denemeleri
- `configs/` – Kafka, Spark ve Qdrant ayarları
- `tests/` – temizlik, embedding ve search testleri
- `docs/` – mimari açıklamalar, pipeline akışı, ekran görüntüleri

### MVP hedefi (V1)

- Hazır dataset’ten yorumları Kafka’ya gönderen bir producer
- Spark Structured Streaming ile Bronze/Silver katmanlarının yazılması
- Silver’daki `review_text` için embedding üretimi
- Embedding’lerin Qdrant’a yazılması
- Komut satırından çağrılabilen basit bir semantic search script’i

İlerleyen aşamalarda:

- FastAPI tabanlı HTTP search API
- Docker Compose ile Kafka + Qdrant + API orkestrasyonu
- Ek testler ve dokümantasyon

