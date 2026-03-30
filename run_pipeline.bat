@echo off
REM Windows PowerShell için streaming pipeline başlatma scripti

echo.
echo 🚀 AI-READY REVIEW PIPELINE BASLATILIYOR
echo ========================================

REM Python venv kontrol et
if not exist "venv\" (
    echo 📦 Virtual environment olusturuluyor...
    python -m venv venv
)

REM Venv aktifleştir
echo 🔌 Virtual environment aktifleştiriliyor...
call venv\Scripts\activate.bat

REM Requirements kur
echo 📚 Python dependencies yukleniyor...
pip install -q -r requirements.txt

REM Kafka producer'ı başlat (arka planda)
echo.
echo 📤 Kafka producer baslatiliyor...
cd producer
start python kafka_producer.py
cd ..

timeout /t 5 /nobreak

REM Streaming pipeline başlat
echo.
echo 🔄 Streaming pipeline baslatiliyor...
cd streaming
python orchestrate_pipeline.py

echo.
echo ✅ Pipeline tamamlandi
pause
