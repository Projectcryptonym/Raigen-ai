# Raigen Backend

FastAPI backend for Raigen with Google Calendar integration, Firestore, and Memory API.

## Setup

### 1. Environment Variables

Copy `env.example` to `.env` and fill in your credentials:

```bash
cp env.example .env
```

Required variables:
- `GOOGLE_CLIENT_ID` - Google OAuth client ID
- `GOOGLE_CLIENT_SECRET` - Google OAuth client secret  
- `GOOGLE_REDIRECT_URI` - OAuth callback URL (http://localhost:8080/auth/google/callback)
- `FIREBASE_PROJECT_ID` - Firebase project ID
- `FIREBASE_SERVICE_ACCOUNT_JSON_BASE64` - Base64-encoded service account JSON

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Test Setup

```bash
python test_setup.py
```

### 4. Run Server

```bash
uvicorn app.main:app --reload --port 8080
```

## API Endpoints

### Authentication
- `GET /auth/google/url` - Get Google OAuth URL
- `POST /auth/google/callback` - Exchange code for refresh token

### Calendar
- `GET /calendar/sync?user_id={user_id}&days={days}` - Sync calendar events
- `POST /calendar/block` - Create/update calendar block

### Plans
- `GET /plan/today?user_id={user_id}` - Get today's plan
- `POST /plan/generate` - Generate new plan with auto free-window discovery
- `POST /plan/replan` - Replan with changes

### Reviews
- `POST /reviews/weekly/generate` - Generate weekly review summary

## Testing

### OAuth Flow
1. Get OAuth URL:
```bash
curl http://localhost:8080/auth/google/url
```

2. Open the `auth_url` in browser, approve, capture the `code`

3. Exchange code for tokens:
```bash
curl -X POST http://localhost:8080/auth/google/callback \
  -H "Content-Type: application/json" \
  -d '{"code":"<PASTE_CODE>","user_id":"test-user-1"}'
```

### Plan Generation with Auto Discovery
```bash
# Generate plan with auto free-window discovery
curl -X POST http://localhost:8080/plan/generate \
  -H "Content-Type: application/json" \
  -d '{
    "user_id":"u1",
    "tasks":[
      {"title":"Deep Work: Pitch","effort_min":120,"urgency":3,"impact":3},
      {"title":"Admin Inbox Zero","effort_min":45,"urgency":2,"impact":1}
    ],
    "free_windows":[],
    "user_prefs":{
      "quiet_hours":{"start":"22:00","end":"07:00"},
      "hard_blocks":[{"label":"work","start":"09:00","end":"17:00","days":[1,2,3,4,5]}],
      "max_day_min":240
    }
  }'

# Get today's plan
curl "http://localhost:8080/plan/today?user_id=u1"

# Generate weekly review
curl -X POST http://localhost:8080/reviews/weekly/generate \
  -H "Content-Type: application/json" \
  -d '{"user_id":"u1"}'
```

### Calendar Operations
```bash
# Sync events
curl "http://localhost:8080/calendar/sync?user_id=test-user-1&days=14"

# Create block
curl -X POST http://localhost:8080/calendar/block \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test-user-1","title":"Deep Work","start_iso":"2025-08-11T13:00:00Z","end_iso":"2025-08-11T15:00:00Z"}'
```

## Architecture

- **FastAPI** - Web framework
- **Google Calendar API** - 2-way calendar sync
- **Firebase/Firestore** - Data persistence
- **Memory API** - MemOS integration (stubbed)
- **OAuth 2.0** - Google authentication

## Next Steps

- Implement scheduler with constraint-aware packing
- Add notification broker (push/email)
- Build weekly review generator
- Create Expo mobile app 