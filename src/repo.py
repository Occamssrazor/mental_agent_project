from sqlalchemy import select
from sqlalchemy.orm import Session
from src.models import User, UserRuntime, Plan, Checkin, PlanNote
from src.config import DEFAULT_TIMEZONE, DEFAULT_DAILY_TIME, DEFAULT_WEEKLY_DAY

def default_plan():
    return {
        "weekly_goal": "Стабилизировать состояние и наладить ритм",
        "daily_steps": [
            "Чек-ин 1 раз в день (1–2 минуты)",
            "Один маленький шаг 2–10 минут",
        ],
        "rules": {
            "if_low_energy": "Сделай микро-версию 2 минуты",
            "if_high_stress": "Сначала техника успокоения 2–4 минуты, потом микро-шаг",
        },
    }

def get_or_create_user(db: Session, tg_chat_id: int) -> User:
    user = db.execute(select(User).where(User.tg_chat_id == tg_chat_id)).scalar_one_or_none()
    if user:
        return user

    user = User(
        tg_chat_id=tg_chat_id,
        timezone=DEFAULT_TIMEZONE,
        daily_time=DEFAULT_DAILY_TIME,
        weekly_day=DEFAULT_WEEKLY_DAY,
        status="active",
    )
    db.add(user)
    db.flush()

    db.add(UserRuntime(user_id=user.id, missing_streak=0, last_nudge_stage=0))
    db.add(Plan(user_id=user.id, plan_json=default_plan()))
    db.commit()
    return user

def get_user_by_id(db: Session, user_id: int) -> User:
    return db.execute(select(User).where(User.id == user_id)).scalar_one()

def get_active_users(db: Session):
    return db.execute(select(User).where(User.status == "active")).scalars().all()

def get_runtime(db: Session, user_id: int) -> UserRuntime:
    return db.execute(select(UserRuntime).where(UserRuntime.user_id == user_id)).scalar_one()

def update_runtime(db: Session, user_id: int, **fields):
    rt = get_runtime(db, user_id)
    for k, v in fields.items():
        setattr(rt, k, v)
    db.add(rt)
    db.commit()

def set_user_status(db: Session, user_id: int, status: str):
    user = get_user_by_id(db, user_id)
    user.status = status
    db.add(user)
    db.commit()

def get_plan(db: Session, user_id: int):
    row = db.execute(select(Plan).where(Plan.user_id == user_id)).scalar_one_or_none()
    return row.plan_json if row and row.plan_json else default_plan()

def save_plan(db: Session, user_id: int, plan_json: dict):
    row = db.execute(select(Plan).where(Plan.user_id == user_id)).scalar_one_or_none()
    if row is None:
        row = Plan(user_id=user_id, plan_json=plan_json)
    else:
        row.plan_json = plan_json
    db.add(row)
    db.commit()

def append_plan_note(db: Session, user_id: int, note: str):
    db.add(PlanNote(user_id=user_id, note=note))
    db.commit()

def upsert_checkin(db: Session, user_id: int, date: str, mood: int, stress: int, energy: int, note: str, tags: list[str]):
    row = db.execute(select(Checkin).where(Checkin.user_id == user_id, Checkin.date == date)).scalar_one_or_none()
    if row is None:
        row = Checkin(user_id=user_id, date=date, mood=mood, stress=stress, energy=energy, note=note, tags={"tags": tags})
    else:
        row.mood, row.stress, row.energy = mood, stress, energy
        row.note = note
        row.tags = {"tags": tags}
    db.add(row)
    db.commit()

def has_checkin_for_date(db: Session, user_id: int, date: str) -> bool:
    return db.execute(select(Checkin.id).where(Checkin.user_id == user_id, Checkin.date == date)).first() is not None

def get_recent_checkins(db: Session, user_id: int, days: int = 7):
    rows = db.execute(select(Checkin).where(Checkin.user_id == user_id).order_by(Checkin.date.desc()).limit(days)).scalars().all()
    return [
        {"date": r.date, "mood": r.mood, "stress": r.stress, "energy": r.energy, "note": r.note or "", "tags": (r.tags or {}).get("tags", [])}
        for r in rows
    ]
