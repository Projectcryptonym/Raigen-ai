#!/usr/bin/env node

/**
 * Test script to verify mobile app API communication
 * Run this to test backend connectivity before running the mobile app
 */

const BASE_URL = process.env.API_URL || "http://localhost:8080";

async function testEndpoint(method, path, body = null) {
  const url = `${BASE_URL}${path}`;
  const options = {
    method,
    headers: {
      'Content-Type': 'application/json',
    },
  };
  
  if (body) {
    options.body = JSON.stringify(body);
  }
  
  try {
    const response = await fetch(url, options);
    const data = await response.json();
    
    if (response.ok) {
      console.log(`✅ ${method} ${path} - Status: ${response.status}`);
      console.log(`   Response: ${JSON.stringify(data, null, 2)}`);
      return true;
    } else {
      console.log(`❌ ${method} ${path} - Status: ${response.status}`);
      console.log(`   Error: ${JSON.stringify(data, null, 2)}`);
      return false;
    }
  } catch (error) {
    console.log(`❌ ${method} ${path} - Network Error: ${error.message}`);
    return false;
  }
}

async function runTests() {
  console.log("🧪 Testing Mobile App API Endpoints...");
  console.log("=" .repeat(60));
  console.log(`🌐 Backend URL: ${BASE_URL}`);
  console.log("");
  
  const tests = [
    // Basic health check
    () => testEndpoint('GET', '/health'),
    
    // User bootstrap
    () => testEndpoint('GET', '/me/bootstrap?user_id=u1'),
    
    // Plan endpoints
    () => testEndpoint('GET', '/plan/today?user_id=u1'),
    () => testEndpoint('POST', '/plan/generate', {
      user_id: 'u1',
      tasks: [
        { title: 'Test Task', effort_min: 30, urgency: 2, impact: 2 }
      ],
      free_windows: [
        { start_iso: '2025-08-11T14:00:00Z', end_iso: '2025-08-11T16:00:00Z' }
      ],
      user_prefs: {
        quiet_hours: { start: '22:00', end: '07:00' },
        hard_blocks: [],
        max_day_min: 300
      }
    }),
    
    // Calendar endpoints
    () => testEndpoint('GET', '/calendar/sync?user_id=u1&days=7'),
    
    // Reviews endpoint
    () => testEndpoint('POST', '/reviews/weekly/generate', { user_id: 'u1' }),
    
    // OAuth URL generation
    () => testEndpoint('GET', '/auth/google/url'),
  ];
  
  let passed = 0;
  let total = tests.length;
  
  for (let i = 0; i < tests.length; i++) {
    const success = await tests[i]();
    if (success) passed++;
    console.log("");
  }
  
  console.log("=" .repeat(60));
  console.log(`🎉 Test Results: ${passed}/${total} passed`);
  
  if (passed === total) {
    console.log("✅ All tests passed! Mobile app should work correctly.");
    console.log("");
    console.log("Next steps:");
    console.log("1. Start the mobile app: cd mobile && npm start");
    console.log("2. Configure Google OAuth in src/auth.ts");
    console.log("3. Test on device or simulator");
  } else {
    console.log("❌ Some tests failed. Check backend server and configuration.");
  }
}

// Run tests
runTests().catch(console.error); 