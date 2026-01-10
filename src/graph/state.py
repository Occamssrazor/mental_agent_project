from typing import TypedDict, Dict, Any, List

class AgentState(TypedDict, total=False):
    user_id: int
    tg_chat_id: int
    timezone: str

    event: str
    text: str

    intent: str

    today: str
    plan: Dict[str, Any]
    checkin: Dict[str, Any]
    branch: str

    rag_top_k: int
    rag_items: List[Dict[str, Any]]

    plan_delta: str
    outgoing: List[str]
