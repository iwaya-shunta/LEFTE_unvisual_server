import os
import base64
from pathlib import Path
from email.mime.text import MIMEText
from typing import Optional
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

BASE_DIR = Path(__file__).resolve().parent.parent
TOKEN_PATH = BASE_DIR / "token.json"

SCOPES = [
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
]

def get_gmail_service():
    """Gmail API への接続を確立します。"""
    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
        return build('gmail', 'v1', credentials=creds)
    return None


def list_unread_emails(max_results: int = 5) -> str:
    """
    最新の未読メールの一覧（送信者、件名、メッセージID）を取得します。

    Args:
        max_results: 取得するメールの最大件数（デフォルト: 5）。
    """
    service = get_gmail_service()
    if not service:
        return "Gmailの認証ができていないみたい。token.json を確認してね。"

    try:
        results = service.users().messages().list(
            userId='me',
            labelIds=['UNREAD'],
            maxResults=max_results
        ).execute()

        messages = results.get('messages', [])
        if not messages:
            return "未読のメールは見当たらないよ！スッキリしてるね。"

        output = []
        for msg in messages:
            m = service.users().messages().get(
                userId='me',
                id=msg['id'],
                format='metadata',
                metadataHeaders=['From', 'Subject', 'Date']
            ).execute()

            headers = m.get('payload', {}).get('headers', [])
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '（件名なし）')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), '不明な差出人')

            output.append(f"ID: {msg['id']} | 差出人: {sender} | 件名: {subject}")

        return "\n".join(output)
    except Exception as e:
        return f"未読メールの取得中にエラーが発生しちゃった：{e}"


def read_email_content(message_id: str) -> str:
    """
    指定されたメッセージIDのメール本文（内容）を取得します。
    メールの一覧を取得した後、特定のメールの詳しい中身を知りたい場合に使用します。

    Args:
        message_id: 読み取りたいメールの固有メッセージID。
    """
    service = get_gmail_service()
    if not service:
        return "Gmailの認証ができていないみたい。"

    try:
        message = service.users().messages().get(userId='me', id=message_id, format='full').execute()
        payload = message.get('payload', {})
        body = ""

        def extract_text(part):
            if part.get('mimeType') == 'text/plain':
                data = part.get('body', {}).get('data', '')
                if data:
                    return base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
            return ""

        parts = payload.get('parts', [])
        if not parts:
            data = payload.get('body', {}).get('data', '')
            if data:
                body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
        else:
            for part in parts:
                body += extract_text(part)
                # ネストされたマルチパート対応
                if 'parts' in part:
                    for subpart in part['parts']:
                        body += extract_text(subpart)

        if not body:
            body = "本文のテキストが見つからなかったよ（HTMLメールなどの可能性があります）。"

        # 音声読み上げやプロンプト肥大化防止のため先頭1000文字程度に制限
        return f"【メール本文（抜粋）】\n{body[:1000]}"
    except Exception as e:
        return f"メール本文の読み取り中にエラーが発生しちゃった：{e}"


def send_email(to_email: str, subject: str, body: str) -> str:
    """
    指定された宛先にメールを送信します。

    Args:
        to_email: 送信先のメールアドレス。
        subject: メールの件名。
        body: 送信する本文。
    """
    service = get_gmail_service()
    if not service:
        return "Gmailの認証ができていないみたい。"

    try:
        message = MIMEText(body)
        message['to'] = to_email
        message['subject'] = subject

        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        service.users().messages().send(userId="me", body={'raw': raw}).execute()
        return f"「{to_email}」宛てにメール「{subject}」を送信したよ！"
    except Exception as e:
        return f"メールの送信に失敗しちゃった：{e}"