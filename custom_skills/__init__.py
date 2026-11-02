from .google_maps_skill import reverse_geocode_skill, search_nearby_places
from .calendar_skill import (
    list_calendar_events,
    add_calendar_event,
    delete_calendar_event,
    update_calendar_event
)
from .gmail_skill import (
    list_unread_emails,
    read_email_content,
    send_email
)
from .web_search_skill import (
    search_web,
    fetch_web_page
)
from .memo_skill import (
    save_memo,
    list_memos,
    delete_memo,
    clear_memos
)

ALL_SKILLS = [
    reverse_geocode_skill,
    search_nearby_places,
    list_calendar_events,
    add_calendar_event,
    delete_calendar_event,
    update_calendar_event,
    list_unread_emails,
    read_email_content,
    send_email,
    search_web,
    fetch_web_page,
    save_memo,
    list_memos,
    delete_memo,
    clear_memos,
]