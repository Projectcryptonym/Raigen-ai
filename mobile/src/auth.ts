import * as AuthSession from "expo-auth-session";
import Constants from "expo-constants";

const GOOGLE_CLIENT_ID = process.env.EXPO_PUBLIC_GOOGLE_CLIENT_ID ?? "<your-web-client-id>";
const REDIRECT = AuthSession.makeRedirectUri({ scheme: "raigen" });

export async function getGoogleAuthUrl() {
  const params = new URLSearchParams({
    client_id: GOOGLE_CLIENT_ID,
    redirect_uri: REDIRECT,
    response_type: "code",
    access_type: "offline",
    prompt: "consent",
    scope: "https://www.googleapis.com/auth/calendar.events",
  }).toString();
  return `https://accounts.google.com/o/oauth2/v2/auth?${params}`;
}

export async function exchangeCode(code: string, userId: string) {
  const api = (await import("./api")).api;
  return api("/auth/google/callback", {
    method: "POST",
    body: JSON.stringify({ code, user_id: userId }),
  });
} 