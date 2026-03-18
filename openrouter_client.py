import os
import requests

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
# Use any allowed model on your OpenRouter account; this one is widely available
OPENROUTER_MODEL = "openai/gpt-4o-mini"

def get_health_advice(user_profile: dict, risk_data: dict) -> str:
    """
    Calls OpenRouter to generate short, actionable advice.
    """
    # Lazy-load the API key each time the function is called
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

    if not OPENROUTER_API_KEY:
        # Fail gracefully if key isn’t present
        return "AI advice unavailable (missing OPENROUTER_API_KEY). Avoid peak pollution hours, wear a certified mask, and minimize outdoor exposure."

    prompt = f"""
You are a concise public-health assistant. Using the profile and risk below, write 3–5 short, actionable tips (bulleted) for the next 24 hours. Be specific about masks, timing, and indoor ventilation. Avoid medical diagnoses.

User Profile:
- Age Group: {user_profile.get('age_group')}
- Condition(s): {user_profile.get('conditions')}
- Location: {user_profile.get('location')}

Risk Summary:
- Category: {risk_data.get('category')}
- Risk Score: {risk_data.get('risk_score')}
- Most Concerning Pollutant: {risk_data.get('worst_pollutant')}
"""

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.4,
    }

    try:
        r = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=30)
        r.raise_for_status()
        data = r.json()
        return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"AI advice temporarily unavailable. Fallback tips: wear a mask outdoors, avoid peak commute hours, and keep windows closed near traffic. (Error: {e})"
