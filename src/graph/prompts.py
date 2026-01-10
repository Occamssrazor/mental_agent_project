PARSE_CHECKIN = """
You are a strict JSON extractor.
Return ONLY: <SOLUTION>JSON</SOLUTION>. No extra text.

If user did not provide numbers 1-10 for mood/stress/energy and you are unsure, set ok=false and ask a short question.

JSON schema:
{
  "ok": true|false,
  "mood": 1..10,
  "stress": 1..10,
  "energy": 1..10,
  "note": "short text",
  "tags": ["work","sleep","relationships","health","study","family","anxiety","motivation"],
  "question": "if ok=false"
}

User message:
{user_text}
"""

COMPOSE_BRANCH = """
Return ONLY: <SOLUTION>JSON</SOLUTION>. No other text.
Write in Russian, short and practical. Avoid medical claims.

Safety rule:
If user mentions self-harm or imminent danger, output:
{"text":"Я вижу, что тебе очень тяжело... (crisis message)","plan_delta":"keep","needs_escalation":true}
But do NOT give instructions for self-harm.

Inputs:
branch: {branch}
checkin: {checkin_json}
plan: {plan_json}
rag: {rag_json}

Rules by branch:
- calm_now: give 1 calming technique (2-4 min) + one tiny follow-up question.
- micro_step: propose a 2-5 minute task aligned with plan + make it feel easy.
- support_reflection: validate feelings + ask one reflective question + suggest one gentle action.
- normal_plan_step: suggest today's plan step (10-20 min) + offer choice (A/B).

JSON schema:
{
  "text": "message to user",
  "plan_delta": "keep|reduce_load|simplify_today",
  "needs_escalation": false
}
"""

WEEKLY_REVIEW = """
Return ONLY: <SOLUTION>JSON</SOLUTION>.
Write in Russian, avoid medical claims.

Input week_checkins and current plan.
Output:
{
  "user_message": "4-7 sentences summary + 2 insights + focus",
  "updated_plan": {
    "weekly_goal": "...",
    "daily_steps": ["...", "...", "..."],
    "rules": {"if_low_energy":"...", "if_high_stress":"..."}
  }
}

week_checkins:
{week_json}

plan:
{plan_json}
"""
