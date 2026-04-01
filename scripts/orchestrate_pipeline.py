"""
ORCHESTRATION - BATCH MODE
Tüm batch streaming job'larını (Bronze, Silver, Gold) sırasıyla çalı    print("\n" + "="*60)
    if success:
        print("✅ PIPELINE TAMAMLANDI!")
        print(f"⏱️  Toplam süre: {elapsed:.1f} saniye")
        print("\n📊 Output Paths:")
        print("  📁 data/bronze/ - Ham veri")
        print("  📁 data/silver/ - Temizlenmiş veri")
        print("  📁 data/gold/reviews/ - Vector DB için ready")
        print("  📁 data/gold/products/ - Product aggregations")
        print("  📁 data/gold/users/ - User aggregations")
        print("  📁 data/embeddings/ - Review embeddings (384-dim vectors)")
    else:
        print("❌ PIPELINE BAŞARISIZ OLDU!")
    print("="*60 + "\n"):
1. Bronze Layer'ı çalıştır - CSV → Bronze Parquet (ham veri)
2. Silver Layer'ı çalıştır - Bronze → Silver Parquet (temizlenmiş veri)
3. Gold Layer'ı çalıştır - Silver → Gold Parquet (agregasyon)

Çıktı:
- data/bronze/ - 568K+ satır ham veri
- data/silver/ - Temizlenmiş, deduplicated veri
- data/gold/reviews/ - Vector DB input
- data/gold/products/ - Product aggregations
- data/gold/users/ - User aggregations
"""
import subprocess
import time
from pathlib import Path


def run_spark_job(job_name, script_path):
    """
    Bir Spark batch job'ını çalıştır ve bitişini bekle
    
    Args:
        job_name: Job adı (logging için)
        script_path: Spark script'in path'i
        
    Returns:
        bool: Başarı durumu
    """
    print(f"\n{'='*60}")
    print(f"▶️  {job_name} çalışıyor...")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(
            ["spark-submit", str(script_path)],
            check=True,
            capture_output=False
        )
        print(f"\n✅ {job_name} başarıyla tamamlandı!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ {job_name} hataya uğradı: {e}")
        return False
    except Exception as e:
        print(f"\n❌ {job_name} çalıştırılamadı: {e}")
        return False


def main():
    """Main - Orchestration"""
    print("\n" + "="*60)
    print("🚀 AI-READY REVIEW PIPELINE - BATCH ORCHESTRATION")
    print("="*60)
    
    # Script path'leri
    base_path = Path(__file__).parent
    bronze_script = base_path / "bronze_layer.py"
    silver_script = base_path / "silver_layer.py"
    gold_script = base_path / "gold_layer.py"
    embedding_script = base_path / "embedding_layer.py"
    
    start_time = time.time()
    
    # Job'ları sırasıyla çalıştır
    print("\n📋 Pipeline Sırası:")
    print("  1️⃣  BRONZE - CSV → Bronze (ham veri)")
    print("  2️⃣  SILVER - Bronze → Silver (temiz veri)")
    print("  3️⃣  GOLD - Silver → Gold (agregasyon + vectors)")
    print("  4️⃣  EMBEDDINGS - Reviews → Vectors (sentence-transformers)")
    
    success = True
    
    # Bronze Layer
    if not run_spark_job("� BRONZE LAYER", bronze_script):
        success = False
    
    time.sleep(2)
    
    # Silver Layer
    if not run_spark_job("🟡 SILVER LAYER", silver_script):
        success = False
    
    time.sleep(2)
    
    # Gold Layer
    if not run_spark_job("🟢 GOLD LAYER", gold_script):
        success = False
    
    time.sleep(2)
    
    # Embedding Layer
    if success:
        if not run_spark_job("🎨 EMBEDDING LAYER", embedding_script):
            success = False
    
    elapsed = time.time() - start_time
    
    print("\n" + "="*60)
    if success:
        print("✅ PIPELINE TAMAMLANDI!")
        print(f"⏱️  Toplam süre: {elapsed:.1f} saniye")
        print("\n📊 Output Paths:")
        print("  📁 data/bronze/ - Ham veri")
        print("  � data/silver/ - Temizlenmiş veri")
        print("  📁 data/gold/reviews/ - Vector DB için ready")
        print("  📁 data/gold/products/ - Product aggregations")
        print("  📁 data/gold/users/ - User aggregations")
    else:
        print("❌ PIPELINE BAŞARISIZ OLDU!")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
