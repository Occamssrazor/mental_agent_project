import requests
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from src.config import TG_BOT_TOKEN

class TgSendArgs(BaseModel):
    tg_chat_id: int
    text: str = Field(..., min_length=1, max_length=4000)

@tool("tg_send", args_schema=TgSendArgs)
def tg_send(tg_chat_id: int, text: str):
    if not TG_BOT_TOKEN:
        print(f"[TG MOCK] {tg_chat_id}: {text}")
        return {"ok": True}

    url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
    r = requests.post(url, json={"chat_id": tg_chat_id, "text": text}, timeout=10)
    r.raise_for_status()
    return {"ok": True}
