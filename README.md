# Big Brother AI

Big Brother is an emotionally intelligent accountability coach that communicates over SMS. It adapts its tone, remembers user context, and proactively checks in when users go silent.

---

## 🔧 System Overview

### `app.py` – Primary AI Coach
- Handles SMS input via Twilio
- Runs onboarding flow (identity, goal, obstacle, tone)
- Detects emotion & domain
- Generates GPT-4o responses using a unified Big Brother voice
- Opportunistically captures user's deeper "why"
- Handles opt-outs and logs user interaction history

### `silence_check.py` – Daily Cron-Based Accountability
- Runs daily at 9AM EST via Render Cron Job
- Checks for users inactive for 48+ hours
- Sends varied silence pings via Twilio
- Escalates tone after 3+ ignores and references user's “why”
- Resets silence_ping_count once the user replies

---

## 🛠 Environment Variables

All services use the following ENV vars (configured in a shared Environment Group on Render):

- `TWILIO_ACCOUNT_SID`
- `TWILIO_AUTH_TOKEN`
- `TWILIO_PHONE_NUMBER`
- `FIREBASE_CREDENTIALS_JSON`

---

## 🧪 Next Ideas / Roadmap

- Streak tracking (days active)
- Confession logging & reflection prompts
- Goal deadline nudging
- Lifetime silence stats & behavior scores
