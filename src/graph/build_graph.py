from langgraph.graph import StateGraph, END
from src.graph.state import AgentState
from src.graph import nodes


def route_event(state: AgentState) -> str:
    return state["event"]


def route_intent(state: AgentState) -> str:
    return state.get("intent", "chat")


def route_checkin_ok(state: AgentState) -> str:
    return "ok" if state.get("checkin", {}).get("ok") else "need_more"


def build_graph(router, retriever):
    g = StateGraph(AgentState)

    # --- nodes ---
    g.add_node("load_plan", nodes.node_load_plan)

    g.add_node("daily_prompt", nodes.node_daily_prompt)
    g.add_node("nudge_24h", nodes.node_nudge_24h)
    g.add_node("nudge_48h", nodes.node_nudge_48h)
    g.add_node("nudge_72h", nodes.node_nudge_72h)

    # NEW: intent -> checkin vs chat
    g.add_node("classify_intent", nodes.node_classify_intent)
    g.add_node("light_chat", lambda s: nodes.node_light_chat(s, router))

    # checkin pipeline
    g.add_node("parse_checkin", lambda s: nodes.node_parse_checkin(s, router))
    g.add_node("ask_missing", nodes.node_ask_missing)
    g.add_node("save_checkin", nodes.node_save_checkin)

    g.add_node("set_branch", nodes.node_set_branch)
    g.add_node("retrieve_rag", lambda s: nodes.node_retrieve_rag(s, retriever))
    g.add_node("compose_branch", lambda s: nodes.node_compose_branch(s, router))
    g.add_node("apply_delta", nodes.node_apply_plan_delta)

    g.add_node("weekly_review", lambda s: nodes.node_weekly_review(s, router))
    g.add_node("send", nodes.node_send)

    # --- entry ---
    g.set_entry_point("load_plan")

    # --- event routing ---
    g.add_conditional_edges("load_plan", route_event, {
        "daily_reminder": "daily_prompt",
        "nudge_24h": "nudge_24h",
        "nudge_48h": "nudge_48h",
        "nudge_72h": "nudge_72h",
        "weekly_review": "weekly_review",
        # IMPORTANT: user_message -> classify_intent (not parse_checkin)
        "user_message": "classify_intent",
    })

    # reminders -> send
    g.add_edge("daily_prompt", "send")
    g.add_edge("nudge_24h", "send")
    g.add_edge("nudge_48h", "send")
    g.add_edge("nudge_72h", "send")

    # --- intent routing ---
    g.add_conditional_edges("classify_intent", route_intent, {
        "checkin": "parse_checkin",
        "chat": "light_chat",
    })

    # chat -> send
    g.add_edge("light_chat", "send")

    # --- checkin routing ---
    g.add_conditional_edges("parse_checkin", route_checkin_ok, {
        "ok": "save_checkin",
        "need_more": "ask_missing",
    })

    g.add_edge("ask_missing", "send")
    g.add_edge("save_checkin", "set_branch")
    g.add_edge("set_branch", "retrieve_rag")
    g.add_edge("retrieve_rag", "compose_branch")
    g.add_edge("compose_branch", "apply_delta")
    g.add_edge("apply_delta", "send")

    # weekly review -> send
    g.add_edge("weekly_review", "send")

    # send -> end
    g.add_edge("send", END)

    return g.compile()

