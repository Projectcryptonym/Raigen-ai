# intents.py

def is_opt_in(msg):
    msg = msg.strip().lower()
    return any(phrase in msg for phrase in [
        "i'm in", "im in", "let's go", "lets go", "i’m ready", "ok", "sure", "ready", "sign me up", "yes", "start"
    ])

def is_opt_out(msg):
    msg = msg.strip().lower()
    return any(phrase in msg for phrase in [
        "i'm out", "im out", "cancel", "stop", "quit", "no", "leave", "unsubscribe"
    ])

def is_silence_response(msg):
    msg = msg.strip().lower()
    return any(phrase in msg for phrase in [
        "still here", "checking in", "i'm back", "im back", "returned"
    ])

def is_goal_response(msg):
    msg = msg.strip().lower()
    return any(phrase in msg for phrase in [
        "my goal", "i want to", "i wanna", "aim", "target", "objective"
    ])

def is_why_response(msg):
    msg = msg.strip().lower()
    return any(phrase in msg for phrase in [
        "because", "my why", "my reason", "purpose", "motivation"
    ])
