"""
Gemini に渡すカスタムスキル（Tool Calling用関数群）の集約モジュール
"""
from custom_skills.calendar_skill import (
    list_calendar_events,
    add_calendar_event,
    delete_calendar_event,
    update_calendar_event,
)
from custom_skills.gmail_skill import (
    list_unread_emails,
    read_email_content,
    send_email,
)
from custom_skills.web_search_skill import (
    search_web,
    fetch_web_page,
)

ALL_SKILLS = [
    # カレンダー
    list_calendar_events,
    add_calendar_event,
    delete_calendar_event,
    update_calendar_event,
    # Gmail
    list_unread_emails,
    read_email_content,
    send_email,
    # Web検索・ブラウジング
    search_web,
    fetch_web_page,
]