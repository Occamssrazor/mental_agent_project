from typing import Dict, Any, List
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from src.db import SessionLocal
from src import repo

class SaveCheckinArgs(BaseModel):
    user_id: int
    date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    mood: int = Field(..., ge=1, le=10)
    stress: int = Field(..., ge=1, le=10)
    energy: int = Field(..., ge=1, le=10)
    note: str = ""
    tags: List[str] = Field(default_factory=list)

@tool("save_checkin", args_schema=SaveCheckinArgs)
def save_checkin(user_id: int, date: str, mood: int, stress: int, energy: int, note: str = "", tags=None):
    db = SessionLocal()
    try:
        repo.upsert_checkin(db, user_id, date, mood, stress, energy, note, tags or [])
        return {"saved": True}
    finally:
        db.close()

class GetRecentCheckinsArgs(BaseModel):
    user_id: int
    days: int = Field(7, ge=1, le=30)

@tool("get_recent_checkins", args_schema=GetRecentCheckinsArgs)
def get_recent_checkins(user_id: int, days: int = 7) -> Dict[str, Any]:
    db = SessionLocal()
    try:
        return {"checkins": repo.get_recent_checkins(db, user_id, days)}
    finally:
        db.close()
