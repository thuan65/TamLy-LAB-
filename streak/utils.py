from datetime import datetime, timedelta, date
from zoneinfo import ZoneInfo
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from models import DailyActivity  

VN_TZ = ZoneInfo("Asia/Ho_Chi_Minh")

def today_vn() -> date:
    return datetime.now(VN_TZ).date()

def _get_or_create_row(db, user_id: int, day: date):
    row = db.execute(
        select(DailyActivity).where(
            DailyActivity.user_id == user_id,
            DailyActivity.day == day
        )
    ).scalar_one_or_none()

    if row:
        return row

    row = DailyActivity(user_id=user_id, day=day)
    db.add(row)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        row = db.execute(
            select(DailyActivity).where(
                DailyActivity.user_id == user_id,
                DailyActivity.day == day
            )
        ).scalar_one()
    return row

def mark_diary(db, user_id: int, day: date | None = None):
    day = day or today_vn()
    row = _get_or_create_row(db, user_id, day)
    if not row.wrote_diary:
        row.wrote_diary = True
        db.commit()

def mark_game(db, user_id: int, day: date | None = None):
    day = day or today_vn()
    row = _get_or_create_row(db, user_id, day)
    if not row.played_game:
        row.played_game = True
        db.commit()

def calc_streak(db, user_id: int):
    day = today_vn()
    streak = 0

    while True:
        row = db.execute(
            select(DailyActivity).where(
                DailyActivity.user_id == user_id,
                DailyActivity.day == day
            )
        ).scalar_one_or_none()

        if not row or not (row.wrote_diary and row.played_game):
            break

        streak += 1
        day = day - timedelta(days=1)

    today_row = db.execute(
        select(DailyActivity).where(
            DailyActivity.user_id == user_id,
            DailyActivity.day == today_vn()
        )
    ).scalar_one_or_none()

    return {
        "streak": streak,
        "today": str(today_vn()),
        "today_wrote_diary": bool(today_row.wrote_diary) if today_row else False,
        "today_played_game": bool(today_row.played_game) if today_row else False,
        "today_done": bool(today_row and today_row.wrote_diary and today_row.played_game),
    }
