import sqlite3
from datetime import date, datetime

DB_PATH = "therapy.db"

def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS diary_streak (
            student_id INTEGER PRIMARY KEY,
            streak INTEGER DEFAULT 0,
            last_date TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS game_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            game TEXT,
            played_at TEXT
        )
    """)

    conn.commit()
    conn.close()