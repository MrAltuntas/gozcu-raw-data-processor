# 📹 Kamera Event Sistemi - Adım 1: Altyapı Kurulumu

## 🎯 Bu Adımda Ne Yapacağız?

Redis ve TimescaleDB servislerini Docker ile ayağa kaldırıp bağlantıları test edeceğiz.

## 📋 Gereksinimler

- Docker & Docker Compose
- Python 3.8+
- pip

## 🚀 Kurulum Adımları

### 1. Docker Servislerini Başlat

```bash
# Servisleri arka planda başlat
docker-compose up -d

# Logları kontrol et (opsiyonel)
docker-compose logs -f

# Servis durumunu kontrol et
docker-compose ps
```

**Beklenen Çıktı:**
```
NAME                  STATUS
camera_redis          Up (healthy)
camera_timescaledb    Up (healthy)
```

### 2. Python Bağımlılıklarını Kur

```bash
pip install -r requirements.txt
```

### 3. Bağlantı Testlerini Çalıştır

```bash
python test_connections.py
```

**Başarılı Çıktı:**
```
============================================================
KAMERA EVENT SİSTEMİ - BAĞLANTI TESTİ
============================================================

[1/2] Redis Testi
------------------------------------------------------------
✓ redis-py kurulu
✓ Redis bağlantısı başarılı
✓ Redis read/write testi başarılı
✓ Redis Stream testi başarılı

[2/2] TimescaleDB Testi
------------------------------------------------------------
✓ psycopg2 kurulu
✓ PostgreSQL bağlantısı başarılı
✓ TimescaleDB extension aktif (versiyon: 2.x.x)
✓ Sorgu testi başarılı

============================================================
✅ TÜM TESTLER BAŞARILI
   Bir sonraki adıma hazırsınız!
============================================================
```

## 🔧 Sorun Giderme

### Redis bağlanamıyor
```bash
# Redis loglarını kontrol et
docker-compose logs redis

# Redis container'ına bağlan
docker exec -it camera_redis redis-cli ping
# Yanıt: PONG
```

### TimescaleDB bağlanamıyor
```bash
# PostgreSQL loglarını kontrol et
docker-compose logs timescaledb

# PostgreSQL container'ına bağlan
docker exec -it camera_timescaledb psql -U postgres -d camera_events
# \dx ile extension'ları listele
```

### Servisleri Yeniden Başlat
```bash
docker-compose down
docker-compose up -d
```

## 📊 Servis Bilgileri

### Redis
- **Port:** 6379
- **Max Memory:** 512MB
- **Persistence:** AOF (Append Only File)
- **Eviction Policy:** allkeys-lru

### TimescaleDB
- **Port:** 5432
- **Database:** camera_events
- **User:** postgres
- **Password:** postgres
- **Max Connections:** 200

## ✅ Sonraki Adım

Testler başarılıysa şunu yazın:
```
"ikinci adıma geçelim"
```

---

**Not:** Bu adım tamamlandıktan sonra şunları yapacağız:
- ✅ Adım 1: Redis + TimescaleDB kurulumu (ŞU AN BURADASINIZ)
- ⏳ Adım 2: Tabloları oluşturma (camera_events_raw, camera_detections_raw)
- ⏳ Adım 3: Test data üretme ve yazma