# Garmin Backend Contract

This app is now wired to hand off Garmin auth and wearable sync through a backend.

## Required environment

Set these on the app side:

```env
EXPO_PUBLIC_API_BASE_URL=https://your-backend.example.com
EXPO_PUBLIC_APP_SCHEME=dialed
```

## Local development before approval

Use the backend starter in `server/README.md`.

Until Garmin approves your app, run the backend in mock mode:

```env
GARMIN_MOCK_MODE=true
```

That gives you:

- a working `/auth/garmin/start` handoff
- connection status from `/api/wearables/connections`
- sample Garmin metrics from `/api/wearables/garmin/latest`
- a mock sync endpoint for local testing

## Auth handoff

The app will open:

```text
GET {API_BASE_URL}/auth/garmin/start?redirect_uri={encoded_app_callback}
```

Example callback:

```text
dialed://auth/garmin
```

## Expected backend responsibilities

1. Redirect the user to Garmin OAuth.
2. Exchange the Garmin auth code for access and refresh tokens.
3. Store tokens server-side by authenticated user.
4. Pull Garmin workout / health data on demand or on a sync schedule.
5. Normalize Garmin payloads into Dialed wearable metrics.
6. Expose connection status and latest sync data back to the app.

## App-facing endpoints

### 1. Start Garmin auth

```http
GET /auth/garmin/start?redirect_uri=dialed%3A%2F%2Fauth%2Fgarmin
```

Behavior:
- starts OAuth
- eventually redirects back to the app callback

### 2. List wearable connections

```http
GET /api/wearables/connections
```

Response:

```json
{
  "connections": [
    {
      "provider": "Garmin",
      "status": "connected",
      "lastSyncAt": "2026-03-19T23:40:00.000Z",
      "accountLabel": "frederick@example.com"
    }
  ]
}
```

### 3. Latest Garmin metrics

```http
GET /api/wearables/garmin/latest
```

Response:

```json
{
  "provider": "Garmin",
  "syncedAt": "2026-03-19T23:40:00.000Z",
  "metrics": {
    "source": "Garmin",
    "durationMinutes": "58",
    "caloriesBurned": "487",
    "averageHeartRate": "141",
    "maxHeartRate": "173",
    "sleepHours": "7.6",
    "recoveryScore": "81"
  }
}
```

### 4. Disconnect Garmin

```http
DELETE /api/wearables/garmin
```

Behavior:
- revoke or invalidate stored tokens where possible
- clear connection status for that user

### 5. Mock Garmin sync for local development

```http
POST /api/wearables/garmin/mock-sync
```

Behavior:
- updates the latest Garmin metrics without Garmin approval
- useful for exercising the app-side analysis flow before live access exists

## Supported connection statuses

Use these exact values:

- `not_connected`
- `setup_required`
- `syncing`
- `connected`
- `error`

## Notes

- Garmin should be treated as the primary provider in the first backend pass.
- The app can already ingest wearable data manually and via payload import.
- Once these endpoints exist, the `Devices` screen can graduate from staged setup to real auto-sync status.
