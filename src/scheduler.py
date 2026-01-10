from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from celery import Celery

from src.config import REDIS_URL, DEFAULT_DAILY_TIME
from src.db import engine, SessionLocal
from src.models import Base
from src import repo
from src.mental_agent import MentalAgent

celery = Celery("mental_agent", broker=REDIS_URL, backend=REDIS_URL)
celery.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)

# Beat schedules: каждую минуту
celery.conf.beat_schedule = {
    "tick-due-reminders-every-minute": {"task": "src.scheduler.tick_due_reminders", "schedule": 60.0},
    "tick-due-nudges-every-minute": {"task": "src.scheduler.tick_due_nudges", "schedule": 60.0},
    "tick-weekly-review-every-minute": {"task": "src.scheduler.tick_weekly_review", "schedule": 60.0},
}

# создаём таблицы (MVP). В проде лучше Alembic.
Base.metadata.create_all(engine)

# Грузим агент один раз в процессе worker'а (это и загрузит LoRA)
_AGENT = None

def get_agent() -> MentalAgent:
    global _AGENT
    if _AGENT is None:
        _AGENT = MentalAgent()
    return _AGENT

@celery.task
def run_graph(user_id: int, event: str, text: str = ""):
    agent = get_agent()
    db = SessionLocal()
    try:
        user = repo.get_user_by_id(db, user_id)
        if user.status != "active":
            return

        state = {
            "user_id": user.id,
            "tg_chat_id": user.tg_chat_id,
            "timezone": user.timezone,
            "event": event,
            "text": text,
            "rag_top_k": 5,
        }
        agent.invoke(state)
    finally:
        db.close()

@celery.task
def tick_due_reminders():
    now_utc = datetime.now(timezone.utc)
    db = SessionLocal()
    try:
        for u in repo.get_active_users(db):
            tz = ZoneInfo(u.timezone or "Europe/Moscow")
            local = now_utc.astimezone(tz)
            hhmm = local.strftime("%H:%M")
            if hhmm != (u.daily_time or DEFAULT_DAILY_TIME):
                continue

            rt = repo.get_runtime(db, u.id)
            if rt.last_reminder_sent_at and (now_utc - rt.last_reminder_sent_at) < timedelta(hours=23):
                continue

            repo.update_runtime(db, u.id, last_reminder_sent_at=now_utc, last_nudge_stage=0)
            run_graph.delay(u.id, "daily_reminder")
    finally:
        db.close()

@celery.task
def tick_due_nudges():
    now_utc = datetime.now(timezone.utc)
    db = SessionLocal()
    try:
        for u in repo.get_active_users(db):
            rt = repo.get_runtime(db, u.id)
            if not rt.last_reminder_sent_at:
                continue

            tz = ZoneInfo(u.timezone or "Europe/Moscow")
            local_today = now_utc.astimezone(tz).date().isoformat()

            if repo.has_checkin_for_date(db, u.id, local_today):
                if rt.last_nudge_stage != 0:
                    repo.update_runtime(db, u.id, last_nudge_stage=0, missing_streak=0)
                continue

            hours = (now_utc - rt.last_reminder_sent_at).total_seconds() / 3600.0
            stage = rt.last_nudge_stage or 0

            if hours >= 72 and stage < 3:
                repo.update_runtime(db, u.id, last_nudge_stage=3, missing_streak=(rt.missing_streak or 0) + 1)
                run_graph.delay(u.id, "nudge_72h")
            elif hours >= 48 and stage < 2:
                repo.update_runtime(db, u.id, last_nudge_stage=2, missing_streak=(rt.missing_streak or 0) + 1)
                run_graph.delay(u.id, "nudge_48h")
            elif hours >= 24 and stage < 1:
                repo.update_runtime(db, u.id, last_nudge_stage=1, missing_streak=(rt.missing_streak or 0) + 1)
                run_graph.delay(u.id, "nudge_24h")
    finally:
        db.close()

@celery.task
def tick_weekly_review():
    now_utc = datetime.now(timezone.utc)
    db = SessionLocal()
    try:
        for u in repo.get_active_users(db):
            tz = ZoneInfo(u.timezone or "Europe/Moscow")
            local = now_utc.astimezone(tz)
            hhmm = local.strftime("%H:%M")
            dow = local.strftime("%a").lower()[:3]  # mon/tue/...

            if dow != (u.weekly_day or "sun"):
                continue
            if hhmm != (u.daily_time or DEFAULT_DAILY_TIME):
                continue

            rt = repo.get_runtime(db, u.id)
            today = local.date().isoformat()
            if rt.last_weekly_review_date == today:
                continue  # защита от дублей в ту же минуту

            repo.update_runtime(db, u.id, last_weekly_review_date=today)
            run_graph.delay(u.id, "weekly_review")
    finally:
        db.close()
