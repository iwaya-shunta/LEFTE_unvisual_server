import sqlite3
from pathlib import Path
from datetime import datetime, timedelta

# 運用中ストレージ chat_history.db を指定
DB_PATH = Path(__file__).resolve().parent / "chat_history.db"


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


def get_recent_messages(limit: int = 50):
    """直近のメッセージを取得（時系列の古い順に並べて返す）"""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, role, content, timestamp, image_url
            FROM (
                SELECT id, role, content, timestamp, image_url
                FROM messages
                ORDER BY id DESC
                LIMIT ?
            ) ORDER BY id ASC
        """, (limit,))
        rows = cursor.fetchall()
        return [
            {
                "id": r["id"],
                "role": r["role"],
                "content": r["content"],
                "timestamp": r["timestamp"],
                "image_url": r["image_url"],
            }
            for r in rows
        ]

def get_history_by_days(days: int = 5):
    """過去指定日数のログを取得する (timestamp, role, content, image_url)"""
    since_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT timestamp, role, content, image_url
            FROM messages
            WHERE timestamp >= ?
            ORDER BY timestamp ASC
        """, (since_date,))
        rows = cursor.fetchall()
        return [(r["timestamp"], r["role"], r["content"], r["image_url"]) for r in rows]