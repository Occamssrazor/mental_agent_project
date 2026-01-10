from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Integer, DateTime, Text, JSON, UniqueConstraint, func, ForeignKey

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tg_chat_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)

    timezone: Mapped[str] = mapped_column(String, default="Europe/Moscow")
    daily_time: Mapped[str] = mapped_column(String, default="13:00")
    weekly_day: Mapped[str] = mapped_column(String, default="sun")
    status: Mapped[str] = mapped_column(String, default="active")  # active/paused

    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())

class UserRuntime(Base):
    __tablename__ = "user_runtime"
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)

    last_checkin_date: Mapped[str | None] = mapped_column(String, nullable=True)  # YYYY-MM-DD
    last_reminder_sent_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)

    missing_streak: Mapped[int] = mapped_column(Integer, default=0)
    last_nudge_stage: Mapped[int] = mapped_column(Integer, default=0)  # 0/1/2/3

    last_weekly_review_date: Mapped[str | None] = mapped_column(String, nullable=True)  # YYYY-MM-DD

class Checkin(Base):
    __tablename__ = "checkins"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    date: Mapped[str] = mapped_column(String, index=True)

    mood: Mapped[int] = mapped_column(Integer)
    stress: Mapped[int] = mapped_column(Integer)
    energy: Mapped[int] = mapped_column(Integer)

    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    tags: Mapped[dict] = mapped_column(JSON, default=dict)

    __table_args__ = (UniqueConstraint("user_id", "date", name="uq_checkin_user_day"),)

class Plan(Base):
    __tablename__ = "plans"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, index=True)
    plan_json: Mapped[dict] = mapped_column(JSON, default=dict)

class PlanNote(Base):
    __tablename__ = "plan_notes"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    ts: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())
    note: Mapped[str] = mapped_column(String, nullable=False)
