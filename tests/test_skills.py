"""
L.E.F.T.E. 全カスタムスキルの単体動作検証用スクリプト
"""
import sys
import datetime
import logging
from pathlib import Path

# lefte_server プロジェクトルート（tests の親フォルダ）を検索パスに追加
SERVER_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SERVER_ROOT))

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def run_test(title: str, func, *args, **kwargs):
    """スキルの実行結果と例外を綺麗に表示するラッパー"""
    print(f"\n{'='*25} [TEST: {title}] {'='*25}")
    try:
        result = func(*args, **kwargs)
        print("【実行結果】:")
        print(result)
        return True
    except Exception as e:
        print(f"【例外エラー】: {e}")
        logging.exception(e)
        return False


def main():
    print("=" * 65)
    print("      L.E.F.T.E. カスタムスキル単体デバッグテスト開始")
    print(f"      ルートディレクトリ: {SERVER_ROOT}")
    print("=" * 65)

    # ----------------------------------------------------
    # 1. 逆ジオコーディング (reverse_geocode_skill)
    # ----------------------------------------------------
    try:
        from custom_skills.reverse_geocode_skill import reverse_geocode_skill
        # 新しく取得した座標（小数第6位程度で十分な精度が出ます）
        run_test(
            "1. 逆ジオコーディング",
            reverse_geocode_skill,
            latitude=34.379809,
            longitude=132.402585
        )
    except Exception as e:
        print(f"\n[SKIP] reverse_geocode_skill テスト失敗: {e}")

    # ----------------------------------------------------
    # 2. Google カレンダー (calendar_skill)
    # ----------------------------------------------------
    try:
        from custom_skills.calendar_skill import list_calendar_events

        # ① 直近（現在時刻以降）の予定テスト
        run_test(
            "2-1. カレンダー予定一覧（直近）",
            list_calendar_events,
            max_results=5
        )

        # ② 当日日付指定のテスト
        jst = datetime.timezone(datetime.timedelta(hours=9))
        today_str = datetime.datetime.now(jst).strftime("%Y-%m-%d")
        run_test(
            f"2-2. カレンダー予定一覧（本日: {today_str}）",
            list_calendar_events,
            max_results=5,
            target_date=today_str
        )
    except Exception as e:
        print(f"\n[SKIP] calendar_skill テスト失敗: {e}")

    # ----------------------------------------------------
    # 3. Gmail (gmail_skill)
    # ----------------------------------------------------
    try:
        from custom_skills.gmail_skill import list_unread_emails
        run_test(
            "3. Gmail 未読メール一覧取得",
            list_unread_emails,
            max_results=3
        )
    except Exception as e:
        print(f"\n[SKIP] gmail_skill テスト失敗: {e}")

    # ----------------------------------------------------
    # 4. Web 検索 & ページ取得 (web_search_skill)
    # ----------------------------------------------------
    try:
        from custom_skills.web_search_skill import search_web, fetch_web_page

        run_test(
            "4-1. Web検索 (DuckDuckGo)",
            search_web,
            query="広島市西区 天気",
            max_results=2
        )
        run_test(
            "4-2. Webページ本文取得",
            fetch_web_page,
            url="https://example.com"
        )
    except Exception as e:
        print(f"\n[SKIP] web_search_skill テスト失敗: {e}")

    print(f"\n{'='*65}\n全スキルの検証が完了しました。\n{'='*65}")

# ----------------------------------------------------
    # 5. 汎用メモ機能 (memo_skill)
    # ----------------------------------------------------
    try:
        from custom_skills.memo_skill import (
            save_memo,
            list_memos,
            delete_memo,
            clear_memos,
        )

        run_test("5-1. 買い物メモ保存", save_memo, content="柚子胡椒を買う", category="shopping")
        run_test("5-2. 一般メモ保存", save_memo, content="Raspberry Piのバックアップを取る")
        run_test("5-3. 全メモ一覧表示", list_memos)
        run_test("5-4. 買い物カテゴリー絞り込み", list_memos, category="shopping")
        run_test("5-5. メモキーワード削除", delete_memo, memo_id_or_keyword="柚子胡椒")
        run_test("5-6. 全メモクリア", clear_memos)
    except Exception as e:
        print(f"\n[SKIP] memo_skill テスト失敗: {e}")



if __name__ == "__main__":
    main()