from pydantic import BaseModel
from langchain_core.tools import tool
from src.db import SessionLocal
from src import repo

class SetStatusArgs(BaseModel):
    user_id: int
    status: str  # active/paused

@tool("set_user_status", args_schema=SetStatusArgs)
def set_user_status(user_id: int, status: str):
    db = SessionLocal()
    try:
        repo.set_user_status(db, user_id, status)
        return {"ok": True}
    finally:
        db.close()
