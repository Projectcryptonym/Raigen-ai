import React, { useEffect, useState } from "react";
import { View, Text, TouchableOpacity, SafeAreaView, FlatList, Platform } from "react-native";
import * as AuthSession from "expo-auth-session";
import * as Linking from "expo-linking";
import * as Notifications from "expo-notifications";
import { api } from "./src/api";
import { getGoogleAuthUrl, exchangeCode } from "./src/auth";

Notifications.setNotificationHandler({ 
  handleNotification: async () => ({ 
    shouldShowAlert: true, 
    shouldPlaySound: false, 
    shouldSetBadge: false 
  }) 
});

async function registerPush() {
  const { status } = await Notifications.requestPermissionsAsync();
  if (status !== "granted") return null;
  const token = (await Notifications.getExpoPushTokenAsync()).data;
  return token;
}

export default function App() {
  const [userId, setUserId] = useState<string>("u1"); // MVP fixed id; replace with real auth later
  const [plan, setPlan] = useState<any>(null);
  const [events, setEvents] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    (async () => {
      const token = await registerPush();
      if (token) {
        try {
          await api("/notify/register", {
            method:"POST",
            body: JSON.stringify({ user_id: userId, expo_push_token: token })
          });
        } catch (e) {
          console.log("register push token failed", e);
        }
      }
    })();
  }, [userId]);

  async function handleConnectGoogle() {
    const authUrl = await getGoogleAuthUrl();
    const result = await AuthSession.startAsync({ authUrl, returnUrl: Linking.createURL("") });
    if (result.type === "success" && result.params?.code) {
      await exchangeCode(result.params.code as string, userId);
      alert("Google connected!");
    } else {
      alert("Google auth canceled or failed");
    }
  }

  async function fetchPlan() {
    const p = await api(`/plan/today?user_id=${userId}`);
    setPlan(p);
  }

  async function generatePlan() {
    setLoading(true);
    try {
      const body = {
        user_id: userId,
        tasks: [
          { title: "Deep Work: Proposal", effort_min: 120, energy: "high", urgency: 3, impact: 3 },
          { title: "Admin Inbox Zero", effort_min: 45, energy: "low", urgency: 2, impact: 1 }
        ],
        free_windows: [], // triggers auto discovery on server
        user_prefs: {
          quiet_hours: { start: "22:00", end: "07:00" },
          hard_blocks: [{ label: "work", start: "09:00", end: "17:00", days: [1,2,3,4,5] }],
          max_day_min: 240
        }
      };
      const r = await api("/plan/generate", { method: "POST", body: JSON.stringify(body) });
      setPlan(r);
    } finally {
      setLoading(false);
    }
  }

  async function syncCalendar() {
    const r = await api(`/calendar/sync?user_id=${userId}&days=7`);
    setEvents(r.events || []);
  }

  return (
    <SafeAreaView style={{ flex:1, padding:16 }}>
      <Text style={{ fontSize:22, fontWeight:"600", marginBottom:12 }}>Raigen</Text>

      <TouchableOpacity onPress={handleConnectGoogle} style={{ padding:12, backgroundColor:"#111", borderRadius:8, marginBottom:10 }}>
        <Text style={{ color:"#fff", textAlign:"center" }}>Connect Google Calendar</Text>
      </TouchableOpacity>

      <TouchableOpacity onPress={generatePlan} disabled={loading} style={{ padding:12, backgroundColor:"#4a90e2", borderRadius:8, marginBottom:10 }}>
        <Text style={{ color:"#fff", textAlign:"center" }}>{loading ? "Generating..." : "Generate Today's Plan"}</Text>
      </TouchableOpacity>

      <TouchableOpacity onPress={fetchPlan} style={{ padding:12, backgroundColor:"#ddd", borderRadius:8, marginBottom:10 }}>
        <Text style={{ textAlign:"center" }}>Fetch Today's Plan</Text>
      </TouchableOpacity>

      <TouchableOpacity onPress={syncCalendar} style={{ padding:12, backgroundColor:"#ddd", borderRadius:8, marginBottom:10 }}>
        <Text style={{ textAlign:"center" }}>Sync Calendar (7 days)</Text>
      </TouchableOpacity>

      <Text style={{ fontSize:18, marginTop:10, marginBottom:4 }}>Today</Text>
      <View style={{ backgroundColor:"#f5f5f5", borderRadius:8, padding:10 }}>
        {plan ? (
          <>
            <Text style={{ fontWeight:"600" }}>{plan.date}</Text>
            {plan.blocks?.length ? plan.blocks.map((b:any, i:number) => (
              <Text key={i} style={{ marginVertical:2 }}>• {b.title} — {b.start} → {b.end}</Text>
            )) : <Text>No blocks yet.</Text>}
            {plan.rationale ? <Text style={{ marginTop:6, fontStyle:"italic" }}>{plan.rationale}</Text> : null}
          </>
        ) : <Text>Tap "Generate Today's Plan".</Text>}
      </View>

      <Text style={{ fontSize:18, marginTop:16, marginBottom:4 }}>Agenda (7 days)</Text>
      <View style={{ backgroundColor:"#f5f5f5", borderRadius:8, padding:10, flex:1 }}>
        <FlatList
          data={events}
          keyExtractor={(item:any) => item.id}
          renderItem={({ item }) => (
            <Text style={{ marginVertical:2 }}>• {item.summary || "(busy)"} — {item.start} → {item.end}</Text>
          )}
          ListEmptyComponent={<Text>No events. Connect Google and Sync.</Text>}
        />
      </View>
    </SafeAreaView>
  );
} 