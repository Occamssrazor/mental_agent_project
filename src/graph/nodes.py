import json
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from src.graph.state import AgentState
from src.graph.prompts import PARSE_CHECKIN, COMPOSE_BRANCH, WEEKLY_REVIEW
from src.tools.plan_tools import get_active_plan, update_plan, append_plan_note
from src.tools.checkin_tools import save_checkin, get_recent_checkins
from src.tools.telegram_tools import tg_send
import re

CHECKIN_NUMS_RE = re.compile(r"\b(10|[1-9])\b")

def looks_like_checkin(text: str) -> bool:
    if not text:
        return False
    t = text.lower()
    if "настро" in t or "стресс" in t or "энерг" in t:
        return True
    nums = CHECKIN_NUMS_RE.findall(t)
    # если пользователь прислал хотя бы 3 числа 1-10 — похоже на чек-ин
    return len(nums) >= 3

def node_classify_intent(state: AgentState) -> AgentState:
    state["intent"] = "checkin" if looks_like_checkin(state.get("text", "")) else "chat"
    return state

def node_light_chat(state: AgentState, router) -> AgentState:
    system = (
        "Ты дружелюбный ассистент. Отвечай по-русски, коротко и практично. "
        "Если пользователь просит совет про психическое состояние — предлагай мягкие, безопасные шаги."
    )
    answer = router.light_chat(system, state.get("text", ""))
    state.setdefault("outgoing", []).append(answer)
    return state

def local_today(tz_name: str) -> str:
    tz = ZoneInfo(tz_name or "Europe/Moscow")
    return datetime.now(timezone.utc).astimezone(tz).date().isoformat()

def node_load_plan(state: AgentState) -> AgentState:
    state.setdefault("outgoing", [])
    state["today"] = local_today(state.get("timezone", "Europe/Moscow"))
    state["plan"] = get_active_plan.invoke({"user_id": state["user_id"]})["plan"]
    return state

def node_daily_prompt(state: AgentState) -> AgentState:
    state["outgoing"].append("Чек-ин: настроение/стресс/энергия (1–10) + 1 строка: что произошло?")
    return state

def node_nudge_24h(state: AgentState) -> AgentState:
    state["outgoing"].append("Если нет ресурса писать много — просто цифры: настроение/стресс/энергия 1–10 (можно без текста).")
    return state

def node_nudge_48h(state: AgentState) -> AgentState:
    state["outgoing"].append("Можно без дневника. Выбери одно: A) 2 минуты дыхания 4–4–6, B) 5 минут прогулки. Что ближе?")
    return state

def node_nudge_72h(state: AgentState) -> AgentState:
    state["outgoing"].append("Хочешь поставить на паузу? Напиши /pause. Или скажи, чтобы я писал реже.")
    return state

def node_parse_checkin(state: AgentState, router) -> AgentState:
    prompt = PARSE_CHECKIN.format(user_text=state.get("text", ""))
    state["checkin"] = router.mental_json(prompt)
    return state

def node_ask_missing(state: AgentState) -> AgentState:
    q = (state.get("checkin") or {}).get("question") or "Оцени, пожалуйста: настроение/стресс/энергия по шкале 1–10."
    state["outgoing"].append(q)
    return state

def node_save_checkin(state: AgentState) -> AgentState:
    c = state["checkin"]
    save_checkin.invoke({
        "user_id": state["user_id"],
        "date": state["today"],
        "mood": int(c["mood"]),
        "stress": int(c["stress"]),
        "energy": int(c["energy"]),
        "note": c.get("note", ""),
        "tags": c.get("tags", []),
    })
    return state

def choose_branch_from_numbers(checkin: dict) -> str:
    mood, stress, energy = int(checkin["mood"]), int(checkin["stress"]), int(checkin["energy"])
    if stress >= 8:
        return "calm_now"
    if energy <= 3:
        return "micro_step"
    if mood <= 3:
        return "support_reflection"
    return "normal_plan_step"

def node_set_branch(state: AgentState) -> AgentState:
    state["branch"] = choose_branch_from_numbers(state["checkin"])
    return state

def node_retrieve_rag(state: AgentState, retriever) -> AgentState:
    # query — смесь чек-ина и заметки
    c = state["checkin"]
    query = f"mood={c.get('mood')} stress={c.get('stress')} energy={c.get('energy')} note={c.get('note','')}"
    state["rag_items"] = retriever.retrieve(query, top_k=int(state.get("rag_top_k", 5)))
    return state

def node_compose_branch(state: AgentState, router) -> AgentState:
    prompt = COMPOSE_BRANCH.format(
        branch=state["branch"],
        checkin_json=json.dumps(state["checkin"], ensure_ascii=False),
        plan_json=json.dumps(state["plan"], ensure_ascii=False),
        rag_json=json.dumps(state.get("rag_items", []), ensure_ascii=False),
    )
    out = router.mental_json(prompt)
    state["plan_delta"] = out.get("plan_delta", "keep")
    state["needs_escalation"] = bool(out.get("needs_escalation", False))
    state["outgoing"].append(out["text"])
    return state

def node_apply_plan_delta(state: AgentState) -> AgentState:
    delta = state.get("plan_delta", "keep")
    if delta == "keep":
        return state

    plan = state["plan"]
    plan.setdefault("rules", {})

    if delta == "reduce_load":
        plan["rules"]["today_mode"] = "light"
        append_plan_note.invoke({"user_id": state["user_id"], "note": "Auto: reduced load due to high stress."})
    elif delta == "simplify_today":
        plan["rules"]["today_mode"] = "micro"
        append_plan_note.invoke({"user_id": state["user_id"], "note": "Auto: simplified today due to low energy."})

    update_plan.invoke({"user_id": state["user_id"], "plan": plan})
    state["plan"] = plan
    return state

def node_weekly_review(state: AgentState, router) -> AgentState:
    week = get_recent_checkins.invoke({"user_id": state["user_id"], "days": 7})["checkins"]
    prompt = WEEKLY_REVIEW.format(
        week_json=json.dumps(week, ensure_ascii=False),
        plan_json=json.dumps(state["plan"], ensure_ascii=False),
    )
    out = router.mental_json(prompt)
    state["outgoing"].append(out["user_message"])
    update_plan.invoke({"user_id": state["user_id"], "plan": out["updated_plan"]})
    state["plan"] = out["updated_plan"]
    return state

def node_send(state: AgentState) -> AgentState:
    for msg in state.get("outgoing", []):
        tg_send.invoke({"tg_chat_id": state["tg_chat_id"], "text": msg})
    state["outgoing"] = []
    return state
