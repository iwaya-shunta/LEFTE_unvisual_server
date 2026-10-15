"""
Gemini に渡すカスタムスキル（Tool Calling用関数群）の集約モジュール
"""
from custom_skills.calendar_skill import (
    list_calendar_events,
    add_calendar_event,
    delete_calendar_event,
    update_calendar_event,
)

# Gemini に渡す全ツールのリスト
ALL_SKILLS = [
    list_calendar_events,
    add_calendar_event,
    delete_calendar_event,
    update_calendar_event,
]