from pathlib import Path
import sqlite3

# ชี้ไปที่ฐานข้อมูลจริงตาม path ของคุณ
DB_FILE = Path(__file__).parent / "data" / "Quetung.db"
print("USING DB FILE:", DB_FILE.resolve())
def get_conn():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


