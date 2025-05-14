import openai
import os

openai.api_key = os.getenv("OPENAI_API_KEY")

INTENT_CATEGORIES = {
    "opt_in": "User wants to begin onboarding or coaching (e.g. 'I'm in', 'Let's start')",
    "opt_out": "User wants to stop, unsubscribe, or cancel",
    "silence": "User has returned or is checking in after absence",
    "goal": "User is sharing a goal or intention (e.g. 'I want to lose weight')",
    "why": "User is sharing motivation, deeper purpose, or emotional context",
    "unknown": "Message does not clearly fit any category"
}

def route_intent(message, user_state=None):
    prompt = f"""
You are an intent classifier for an AI life coach named Raigen.
The user sent this message: "{message}"

Choose the single best matching intent from this list:
{chr(10).join([f"- {k}: {v}" for k, v in INTENT_CATEGORIES.items()])}

Respond ONLY with the intent key (e.g. 'opt_in').
Do not explain or add any extra text.
"""

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",  # Use 4o mini (cheaper, faster, accurate)
            messages=[{"role": "system", "content": prompt}],
            temperature=0,
            max_tokens=5
        )

        intent = response.choices[0].message.content.strip()
        handler = f"handle_{intent}" if intent in INTENT_CATEGORIES else "handle_unknown"
        return intent, handler

    except Exception as e:
        print(f"[Intent Routing Error] {e}")
        return "unknown", "handle_unknown"
