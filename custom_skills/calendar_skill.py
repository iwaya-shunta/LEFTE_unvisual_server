import os
import datetime
from pathlib import Path
from typing import Optional
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from dotenv import load_dotenv

load_dotenv()

# WSLプロジェクト直下または指定フォルダにある token.json を参照
BASE_DIR = Path(__file__).resolve().parent.parent
TOKEN_PATH = BASE_DIR / "token.json"

SCOPES = ['https://www.googleapis.com/auth/calendar']
# .env から取得（未設定なら primary）
USER_EMAIL = os.getenv("GOOGLE_USER_EMAIL", "primary")


def get_calendar_service():
    """Google Calendar API への接続を確立します。"""
    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
        return build('calendar', 'v3', credentials=creds)
    return None


def list_calendar_events(
    max_results: int = 10,
    target_date: Optional[str] = None
) -> str:
    """
    Googleカレンダーから予定を取得します。
    特定の日付の予定を確認したい場合や、直近の予定一覧を見たい場合に使用します。

    Args:
        max_results: 取得する予定の最大件数（デフォルト: 10）。
        target_date: 特定の日付の予定を取得したい場合に指定 (形式: YYYY-MM-DD)。
                     指定しない場合は現在時刻以降の直近の予定を取得します。
    """
    service = get_calendar_service()
    if not service:
        return "カレンダーの認証ができていないみたい。token.json を確認してね。"

    # 日本標準時 (JST: UTC+9)
    jst = datetime.timezone(datetime.timedelta(hours=9))

    try:
        if target_date:
            # 特定日付の 00:00:00 〜 23:59:59 を範囲指定
            dt = datetime.datetime.strptime(target_date, "%Y-%m-%d")
            time_min = dt.replace(hour=0, minute=0, second=0, tzinfo=jst).isoformat()
            time_max = dt.replace(hour=23, minute=59, second=59, tzinfo=jst).isoformat()
        else:
            # 現在時刻以降
            time_min = datetime.datetime.now(jst).isoformat()
            time_max = None

        events_result = service.events().list(
            calendarId=USER_EMAIL,
            timeMin=time_min,
            timeMax=time_max,
            maxResults=max_results,
            singleEvents=True,
            orderBy='startTime'
        ).execute()

        events = events_result.get('items', [])
        if not events:
            date_label = f"{target_date} の" if target_date else "直近の"
            return f"{date_label}予定は何も入っていないよ！"

        results = []
        for e in events:
            start = e['start'].get('dateTime', e['start'].get('date'))
            summary = e.get('summary', '無題')
            results.append(f"件名: {summary} | 開始: {start}")

        return "\n".join(results)
    except Exception as e:
        return f"予定の取得中にエラーが発生しちゃった：{e}"


def add_calendar_event(summary: str, start_time: str, end_time: str, description: str = "") -> str:
    """
    新しい予定をカレンダーに追加します。
    summary: 予定の件名
    start_time: 開始時刻 (ISO 8601形式: YYYY-MM-DDTHH:MM:SS+09:00)
    end_time: 終了時刻 (ISO 8601形式: YYYY-MM-DDTHH:MM:SS+09:00)
    description: 予定の詳細な説明（任意）
    """
    service = get_calendar_service()
    if not service:
        return "カレンダーの認証ができていないみたい。"

    try:
        event = {
            'summary': summary,
            'description': description,
            'start': {'dateTime': start_time, 'timeZone': 'Asia/Tokyo'},
            'end': {'dateTime': end_time, 'timeZone': 'Asia/Tokyo'},
        }
        result = service.events().insert(calendarId=USER_EMAIL, body=event).execute()
        return f"予定「{summary}」を追加したよ！"
    except Exception as e:
        return f"予定の追加に失敗しちゃった：{e}"


def delete_calendar_event(event_id: str) -> str:
    """
    指定された ID を持つ予定を削除します。
    event_id: 削除したい予定の固有ID。
    """
    service = get_calendar_service()
    if not service:
        return "カレンダーの認証ができていないみたい。"

    try:
        service.events().delete(calendarId=USER_EMAIL, eventId=event_id).execute()
        return f"予定を削除したよ！"
    except Exception as e:
        return f"予定の削除に失敗しちゃった：{e}"


def update_calendar_event(event_id: str, summary: Optional[str] = None, start_time: Optional[str] = None, end_time: Optional[str] = None) -> str:
    """
    既存の予定の内容を更新します。
    event_id: 更新したい予定の固有ID。
    summary: 新しい件名（変更する場合のみ指定）
    start_time: 新しい開始時刻（変更する場合のみ指定）
    end_time: 新しい終了時刻（変更する場合のみ指定）
    """
    service = get_calendar_service()
    if not service:
        return "カレンダーの認証ができていないみたい。"

    try:
        event = service.events().get(calendarId=USER_EMAIL, eventId=event_id).execute()
        if summary:
            event['summary'] = summary
        if start_time:
            event['start']['dateTime'] = start_time
        if end_time:
            event['end']['dateTime'] = end_time

        result = service.events().update(calendarId=USER_EMAIL, eventId=event_id, body=event).execute()
        return f"予定を「{result.get('summary')}」に更新したよ！"
    except Exception as e:
        return f"予定の更新に失敗しちゃった：{e}"