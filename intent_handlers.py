# intent_handlers.py

from twilio.twiml.messaging_response import MessagingResponse

ONBOARDING_LINK = "https://yourdomain.com/start"  # Replace with your actual onboarding URL

def handle_opt_in(user_phone):
    resp = MessagingResponse()
    resp.message(f"Awesome. Start here → {ONBOARDING_LINK}")
    return str(resp)

def handle_opt_out(user_phone):
    resp = MessagingResponse()
    resp.message("Understood. You won’t receive messages from Raigen going forward.")
    return str(resp)

def handle_goal(user_phone):
    resp = MessagingResponse()
    resp.message("Got it. That sounds like a strong direction. Raigen will use this to shape your path.")
    return str(resp)

def handle_why(user_phone):
    resp = MessagingResponse()
    resp.message("Purpose matters. Want to write it down? Reflect on your why in 1 sentence.")
    return str(resp)

def handle_silence(user_phone):
    resp = MessagingResponse()
    resp.message("Still here. No pressure — when you’re ready, we’ll pick it back up.")
    return str(resp)

def handle_unknown(user_phone):
    resp = MessagingResponse()
    resp.message("Wasn’t sure how to respond to that — but I’m here. Want to start your journey?")
    return str(resp)

