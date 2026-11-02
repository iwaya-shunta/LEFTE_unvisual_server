import sqlite3
from pathlib import Path
from typing import Optional

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "lefte.db"


def _init_memo_table():
    """メモ用のテーブルを初期化"""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS memos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                category TEXT DEFAULT 'general',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()


def save_memo(content: str, category: str = "general") -> str:
    """
    覚えておいてほしい内容やメモを保存します。
    買い物リスト、アイデア、タスク、備忘録などを記録したい場合に使用します。

    Args:
        content: 覚えさせたいメモの具体的な内容（例: "柚子胡椒を買う", "次回の釣行は若潮の満潮狙い", "サーバーのポート開放確認"）。
        category: メモの分類（例: "shopping", "idea", "todo", "general" など、省略可）。
    """
    _init_memo_table()
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO memos (content, category) VALUES (?, ?)",
                (content.strip(), category.strip()),
            )
            conn.commit()
        return f"「{content}」をメモにしっかり記録したよ！"
    except Exception as e:
        return f"メモの保存中にエラーが発生しちゃった：{e}"


def list_memos(category: Optional[str] = None) -> str:
    """
    保存されているメモの一覧を取得します。
    「何をメモしてたっけ？」「買い物リストを見せて」「アイデア一覧を出して」などと聞かれた場合に使用します。

    Args:
        category: 特定のカテゴリーのみ取得したい場合に指定（例: "shopping", "todo" など。指定しない場合は全メモを取得）。
    """
    _init_memo_table()
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            if category:
                cursor.execute(
                    "SELECT id, content, category, created_at FROM memos WHERE category = ? ORDER BY id ASC",
                    (category.strip(),),
                )
            else:
                cursor.execute(
                    "SELECT id, content, category, created_at FROM memos ORDER BY id ASC"
                )
            rows = cursor.fetchall()

        if not rows:
            target_str = f"「{category}」の" if category else ""
            return f"現在、{target_str}メモには何も残っていないよ！"

        output = ["【保存されているメモ一覧】"]
        for memo_id, content, cat, _ in rows:
            cat_label = f"[{cat}] " if cat != "general" else ""
            output.append(f"- (ID:{memo_id}) {cat_label}{content}")

        return "\n".join(output)
    except Exception as e:
        return f"メモの取得中にエラーが発生しちゃった：{e}"


def delete_memo(memo_id_or_keyword: str) -> str:
    """
    不要になったメモや完了したメモを削除します。
    ID（例: "1"）またはメモに含まれるキーワード（例: "柚子胡椒"）で指定できます。

    Args:
        memo_id_or_keyword: 削除したいメモのID、またはメモに含まれる単語や文言。
    """
    _init_memo_table()
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            # 数値ならID削除、文字列ならキーワードあいまい削除
            if memo_id_or_keyword.isdigit():
                cursor.execute("DELETE FROM memos WHERE id = ?", (int(memo_id_or_keyword),))
            else:
                cursor.execute(
                    "DELETE FROM memos WHERE content LIKE ?",
                    (f"%{memo_id_or_keyword.strip()}%",),
                )
            deleted_count = cursor.rowcount
            conn.commit()

        if deleted_count > 0:
            return f"メモ（{memo_id_or_keyword}）を削除したよ！"
        else:
            return f"「{memo_id_or_keyword}」に該当するメモは見つからなかったよ。"
    except Exception as e:
        return f"メモの削除中にエラーが発生しちゃった：{e}"


def clear_memos(category: Optional[str] = None) -> str:
    """
    メモを一括削除します。カテゴリーを指定するとその分類のみ全消去します。

    Args:
        category: 削除したい特定のカテゴリー（省略時はすべてのメモを完全消去）。
    """
    _init_memo_table()
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            if category:
                cursor.execute("DELETE FROM memos WHERE category = ?", (category.strip(),))
                target = f"「{category}」のメモ"
            else:
                cursor.execute("DELETE FROM memos")
                target = "すべてのメモ"
            conn.commit()
        return f"{target}を綺麗にリセットしたよ！"
    except Exception as e:
        return f"メモのリセット中にエラーが発生しちゃった：{e}"