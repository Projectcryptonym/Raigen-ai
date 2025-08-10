# Raigen Mobile App

Expo React Native app for Raigen with Google OAuth, plan generation, and calendar sync.

## Setup

### 1. Install Dependencies

```bash
cd mobile
npm install
```

### 2. Configure Environment

Update `app.config.js` with your settings:

```javascript
export default {
  expo: {
    // ... other config
    extra: {
      EXPO_PUBLIC_API_URL: "http://YOUR_BACKEND_URL:8080"  // Use LAN IP if on device
    }
  }
};
```

Update `src/auth.ts` with your Google OAuth client ID:

```typescript
const GOOGLE_CLIENT_ID = process.env.EXPO_PUBLIC_GOOGLE_CLIENT_ID ?? "YOUR_GOOGLE_WEB_CLIENT_ID";
```

### 3. Google OAuth Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project or select existing
3. Enable Google Calendar API
4. Create OAuth 2.0 credentials
5. Add authorized redirect URIs:
   - `raigen://` (for mobile app)
   - `http://localhost:8080/auth/google/callback` (for backend)

### 4. Run the App

```bash
# Start Expo development server
npm start

# Press 'i' for iOS simulator or 'a' for Android
# Or scan QR code with Expo Go app on your device
```

## Features

- **Google OAuth**: Connect your Google Calendar
- **Plan Generation**: Auto-discover free windows and create optimized plans
- **Calendar Sync**: View your agenda for the next 7 days
- **Push Notifications**: Get notified when plans are generated
- **Today View**: See your current day's plan with rationale

## API Integration

The app connects to the Raigen backend API:

- `/auth/google/callback` - OAuth token exchange
- `/plan/generate` - Generate today's plan with auto discovery
- `/plan/today` - Fetch today's plan
- `/calendar/sync` - Sync calendar events
- `/me/bootstrap` - Get user preferences and capabilities

## Development

### Project Structure

```
mobile/
├── App.tsx              # Main app component
├── app.config.js        # Expo configuration
├── package.json         # Dependencies
├── src/
│   ├── api.ts          # API client
│   └── auth.ts         # Google OAuth helpers
└── README.md           # This file
```

### Key Components

- **App.tsx**: Main UI with buttons for Google auth, plan generation, and calendar sync
- **api.ts**: HTTP client for backend communication
- **auth.ts**: Google OAuth URL generation and code exchange

## Troubleshooting

### Common Issues

1. **"Cannot connect to backend"**
   - Ensure backend is running on port 8080
   - Check `EXPO_PUBLIC_API_URL` in app.config.js
   - Use LAN IP if testing on physical device

2. **"Google OAuth failed"**
   - Verify Google client ID in src/auth.ts
   - Check redirect URIs in Google Cloud Console
   - Ensure backend OAuth callback endpoint is working

3. **"Plan generation fails"**
   - Check if user has Google Calendar connected
   - Verify backend has real Google/Firebase credentials
   - Check server logs for detailed error messages

### Debug Mode

```bash
# Enable debug logging
EXPO_DEBUG=1 npm start
```

## Next Steps

- Real user authentication (replace fixed user_id)
- Goals management and task creation
- Push notification service integration
- Voice notes with 11labs
- Deep calendar integration 