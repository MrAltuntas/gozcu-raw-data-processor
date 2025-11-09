"""
Yardımcı fonksiyonlar ve utility sınıfları
"""
import redis
import psycopg2
from psycopg2.extras import execute_values
from typing import Dict, List, Any, Optional
import json
from datetime import datetime
import os


class RedisClient:
    """Redis bağlantı ve işlem yöneticisi"""

    def __init__(self, host: str = 'localhost', port: int = 6379, db: int = 0):
        """
        Redis client başlat

        Args:
            host: Redis sunucu adresi
            port: Redis port numarası
            db: Redis veritabanı numarası
        """
        self.client = redis.Redis(
            host=host,
            port=port,
            db=db,
            decode_responses=True
        )

    def is_connected(self) -> bool:
        """Redis bağlantısını kontrol et"""
        try:
            return self.client.ping()
        except redis.ConnectionError:
            return False

    def add_to_stream(self, stream_name: str, data: Dict[str, Any]) -> str:
        """
        Redis stream'e veri ekle

        Args:
            stream_name: Stream adı
            data: Eklenecek veri (dict)

        Returns:
            Message ID
        """
        return self.client.xadd(stream_name, data)

    def read_from_stream(self, stream_name: str, last_id: str = '0',
                        count: int = 100, block: Optional[int] = None) -> List:
        """
        Redis stream'den veri oku

        Args:
            stream_name: Stream adı
            last_id: Son okunan mesaj ID'si
            count: Okunacak mesaj sayısı
            block: Bloke etme süresi (ms), None ise blokesiz

        Returns:
            Mesaj listesi
        """
        return self.client.xread(
            {stream_name: last_id},
            count=count,
            block=block
        )

    def set_key(self, key: str, value: Any, expiry: Optional[int] = None) -> bool:
        """
        Redis'e key-value çifti kaydet

        Args:
            key: Anahtar
            value: Değer
            expiry: Geçerlilik süresi (saniye)

        Returns:
            Başarı durumu
        """
        return self.client.set(key, value, ex=expiry)

    def get_key(self, key: str) -> Optional[str]:
        """Redis'ten değer oku"""
        return self.client.get(key)

    def close(self):
        """Bağlantıyı kapat"""
        self.client.close()


class TimescaleDBClient:
    """TimescaleDB bağlantı ve işlem yöneticisi"""

    def __init__(self, host: str = 'localhost', port: int = 5432,
                 dbname: str = 'camera_events', user: str = 'postgres',
                 password: str = 'postgres'):
        """
        TimescaleDB client başlat

        Args:
            host: PostgreSQL sunucu adresi
            port: PostgreSQL port numarası
            dbname: Veritabanı adı
            user: Kullanıcı adı
            password: Şifre
        """
        self.conn_params = {
            'host': host,
            'port': port,
            'dbname': dbname,
            'user': user,
            'password': password
        }
        self.conn = None
        self.cursor = None

    def connect(self) -> bool:
        """Veritabanına bağlan"""
        try:
            self.conn = psycopg2.connect(**self.conn_params)
            self.cursor = self.conn.cursor()
            return True
        except psycopg2.Error as e:
            print(f"Bağlantı hatası: {e}")
            return False

    def is_connected(self) -> bool:
        """Bağlantı durumunu kontrol et"""
        if not self.conn:
            return False
        try:
            self.cursor.execute("SELECT 1")
            return True
        except:
            return False

    def execute_query(self, query: str, params: Optional[tuple] = None) -> bool:
        """
        SQL sorgusu çalıştır (INSERT, UPDATE, DELETE)

        Args:
            query: SQL sorgusu
            params: Sorgu parametreleri

        Returns:
            Başarı durumu
        """
        try:
            self.cursor.execute(query, params)
            self.conn.commit()
            return True
        except psycopg2.Error as e:
            self.conn.rollback()
            print(f"Sorgu hatası: {e}")
            return False

    def fetch_query(self, query: str, params: Optional[tuple] = None) -> Optional[List]:
        """
        SQL sorgusu çalıştır ve sonuçları getir (SELECT)

        Args:
            query: SQL sorgusu
            params: Sorgu parametreleri

        Returns:
            Sorgu sonuçları
        """
        try:
            self.cursor.execute(query, params)
            return self.cursor.fetchall()
        except psycopg2.Error as e:
            print(f"Sorgu hatası: {e}")
            return None

    def bulk_insert(self, table: str, columns: List[str], data: List[tuple]) -> bool:
        """
        Toplu veri ekleme

        Args:
            table: Tablo adı
            columns: Sütun adları
            data: Eklenecek veriler (tuple listesi)

        Returns:
            Başarı durumu
        """
        try:
            cols = ', '.join(columns)
            query = f"INSERT INTO {table} ({cols}) VALUES %s"
            execute_values(self.cursor, query, data)
            self.conn.commit()
            return True
        except psycopg2.Error as e:
            self.conn.rollback()
            print(f"Toplu ekleme hatası: {e}")
            return False

    def close(self):
        """Bağlantıyı kapat"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()


def load_env_variables() -> Dict[str, str]:
    """
    Çevre değişkenlerini yükle

    Returns:
        Çevre değişkenleri dictionary'si
    """
    return {
        'REDIS_HOST': os.getenv('REDIS_HOST', 'localhost'),
        'REDIS_PORT': int(os.getenv('REDIS_PORT', 6379)),
        'REDIS_DB': int(os.getenv('REDIS_DB', 0)),
        'POSTGRES_HOST': os.getenv('POSTGRES_HOST', 'localhost'),
        'POSTGRES_PORT': int(os.getenv('POSTGRES_PORT', 5432)),
        'POSTGRES_DB': os.getenv('POSTGRES_DB', 'camera_events'),
        'POSTGRES_USER': os.getenv('POSTGRES_USER', 'postgres'),
        'POSTGRES_PASSWORD': os.getenv('POSTGRES_PASSWORD', 'postgres'),
    }


def format_timestamp(dt: datetime) -> str:
    """
    Datetime'ı ISO formatına çevir

    Args:
        dt: datetime objesi

    Returns:
        ISO format string
    """
    return dt.isoformat()


def parse_json_safe(json_str: str) -> Optional[Dict]:
    """
    JSON string'i güvenli şekilde parse et

    Args:
        json_str: JSON string

    Returns:
        Parse edilmiş dictionary veya None
    """
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"JSON parse hatası: {e}")
        return None


def validate_camera_event(event: Dict[str, Any]) -> bool:
    """
    Kamera event verisinin geçerliliğini kontrol et

    Args:
        event: Event verisi

    Returns:
        Geçerlilik durumu
    """
    required_fields = ['camera_id', 'timestamp', 'event_type']
    return all(field in event for field in required_fields)


def get_redis_client() -> RedisClient:
    """Redis client instance'ı oluştur"""
    env = load_env_variables()
    return RedisClient(
        host=env['REDIS_HOST'],
        port=env['REDIS_PORT'],
        db=env['REDIS_DB']
    )


def get_timescaledb_client() -> TimescaleDBClient:
    """TimescaleDB client instance'ı oluştur"""
    env = load_env_variables()
    return TimescaleDBClient(
        host=env['POSTGRES_HOST'],
        port=env['POSTGRES_PORT'],
        dbname=env['POSTGRES_DB'],
        user=env['POSTGRES_USER'],
        password=env['POSTGRES_PASSWORD']
    )
