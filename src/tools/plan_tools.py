from typing import Dict, Any
from pydantic import BaseModel
from langchain_core.tools import tool
from src.db import SessionLocal
from src import repo

class GetPlanArgs(BaseModel):
    user_id: int

@tool("get_active_plan", args_schema=GetPlanArgs)
def get_active_plan(user_id: int) -> Dict[str, Any]:
    db = SessionLocal()
    try:
        return {"plan": repo.get_plan(db, user_id)}
    finally:
        db.close()

class UpdatePlanArgs(BaseModel):
    user_id: int
    plan: Dict[str, Any]

@tool("update_plan", args_schema=UpdatePlanArgs)
def update_plan(user_id: int, plan: Dict[str, Any]):
    db = SessionLocal()
    try:
        repo.save_plan(db, user_id, plan)
        return {"updated": True}
    finally:
        db.close()

class AppendPlanNoteArgs(BaseModel):
    user_id: int
    note: str

@tool("append_plan_note", args_schema=AppendPlanNoteArgs)
def append_plan_note(user_id: int, note: str):
    db = SessionLocal()
    try:
        repo.append_plan_note(db, user_id, note)
        return {"ok": True}
    finally:
        db.close()
