import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "users.db"

print("Using DB at:", DB_PATH)

conn = sqlite3.connect(DB_PATH, check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS gmail_tokens (
    user_id TEXT PRIMARY KEY,
    gmail_email TEXT,
    refresh_token TEXT
)
""")

conn.commit()