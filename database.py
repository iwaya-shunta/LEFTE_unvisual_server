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

def get_today_messages():
    """
    朝4時を1日の境目として、画面表示用の当日メッセージ履歴を取得する
    （現在が午前4時前なら前日4:00以降、午前4時以降なら当日4:00以降）
    """
    now = datetime.now()
    if now.hour < 4:
        # 深夜0:00〜3:59までは「前日の朝4:00」を起点とする
        start_date = (now - timedelta(days=1)).date()
    else:
        # 朝4:00以降は「今日の朝4:00」を起点とする
        start_date = now.date()

    cutoff_time = datetime.combine(start_date, datetime.min.time()).replace(hour=4).strftime("%Y-%m-%d %H:%M:%S")

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, role, content, timestamp, image_url
            FROM messages
            WHERE timestamp >= ?
            ORDER BY id ASC
        """, (cutoff_time,))
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