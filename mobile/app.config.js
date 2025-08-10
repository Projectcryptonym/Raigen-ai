export default {
  expo: {
    name: "Raigen",
    slug: "raigen",
    scheme: "raigen",
    extra: {},
    plugins: ["expo-notifications"],
    experiments: { typedRoutes: false },
    ios: { supportsTablet: true },
    android: {},
    web: {},
    runtimeVersion: { policy: "appVersion" },
    updates: { url: "" },
    extra: {
      EXPO_PUBLIC_API_URL: "http://localhost:8080"
    }
  }
}; 