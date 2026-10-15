import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).resolve().parent / "lefte.db"


def init_db():
    """データベースと messages テーブルの初期化"""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                image_url TEXT
            )
        """)
        conn.commit()


def save_message(role: str, content: str, image_url: str = None):
    """メッセージを messages テーブルに保存"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO messages (role, content, timestamp, image_url)
            VALUES (?, ?, ?, ?)
        """, (role, content, now, image_url))
        conn.commit()


def get_recent_messages(limit: int = 30):
    """直近のメッセージを取得（古い順に並べ直して返す）"""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        # 最新のN件を取得
        cursor.execute("""
            SELECT role, content, timestamp
            FROM messages
            ORDER BY id DESC
            LIMIT ?
        """, (limit,))
        rows = cursor.fetchall()
        # UI表示用に「古い順」に反転
        return rows[::-1]