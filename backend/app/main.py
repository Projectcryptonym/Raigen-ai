from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

app = FastAPI(title="Raigen Backend", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten later
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import and register routes
from .routes import auth, calendar, plan, reviews, me, goals, notify, budgets

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(calendar.router, prefix="/calendar", tags=["calendar"])
app.include_router(plan.router, prefix="/plan", tags=["plan"])
app.include_router(reviews.router, prefix="/reviews", tags=["reviews"])
app.include_router(me.router, prefix="/me", tags=["me"])
app.include_router(goals.router, prefix="/goals", tags=["goals"])
app.include_router(notify.router, prefix="/notify", tags=["notify"])
app.include_router(budgets.router, prefix="/budgets", tags=["budgets"])

@app.get("/")
async def root():
    return {"message": "Raigen Backend is running! 🚀"}

@app.get("/health")
async def health():
    return {"status": "healthy"} 