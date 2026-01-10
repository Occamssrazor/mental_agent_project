from fastapi import FastAPI, Request, Header, HTTPException
from src.config import TG_WEBHOOK_SECRET
from src.db import engine, SessionLocal
from src.models import Base
from src import repo
from src.scheduler import run_graph
from src.tools.user_tools import set_user_status
from src.tools.plan_tools import get_active_plan
from src.tools.telegram_tools import tg_send

Base.metadata.create_all(engine)

app = FastAPI()

def extract_update(update: dict):
    msg = update.get("message") or update.get("edited_message") or {}
    text = msg.get("text")
    chat_id = (msg.get("chat") or {}).get("id")
    return chat_id, text

@app.get("/health")
async def health():
    return {"ok": True}

@app.post("/tg/webhook")
async def tg_webhook(req: Request, x_telegram_bot_api_secret_token: str | None = Header(default=None)):
    # optional secret check
    if TG_WEBHOOK_SECRET:
        if x_telegram_bot_api_secret_token != TG_WEBHOOK_SECRET:
            raise HTTPException(status_code=401, detail="Bad secret")

    update = await req.json()
    chat_id, text = extract_update(update)
    if not chat_id or not text:
        return {"ok": True}

    db = SessionLocal()
    try:
        user = repo.get_or_create_user(db, tg_chat_id=int(chat_id))
        user_id = user.id
    finally:
        db.close()

    t = text.strip()

    if t == "/pause":
        set_user_status.invoke({"user_id": user_id, "status": "paused"})
        tg_send.invoke({"tg_chat_id": chat_id, "text": "Ок, поставила на паузу. Чтобы продолжить — /resume."})
        return {"ok": True}

    if t == "/resume":
        set_user_status.invoke({"user_id": user_id, "status": "active"})
        tg_send.invoke({"tg_chat_id": chat_id, "text": "Ок, снова активна. Можешь написать чек-ин в любом виде."})
        return {"ok": True}

    if t == "/plan":
        plan = get_active_plan.invoke({"user_id": user_id})["plan"]
        msg = "Текущий план:\n"
        msg += f"- Цель недели: {plan.get('weekly_goal','')}\n"
        steps = plan.get("daily_steps", [])
        if steps:
            msg += "- Шаги:\n  " + "\n  ".join(steps)
        tg_send.invoke({"tg_chat_id": chat_id, "text": msg})
        return {"ok": True}

    # обычное сообщение
    run_graph.delay(user_id, "user_message", text=t)
    return {"ok": True}
