# Render Backend Deploy

This is the fastest path to make Dialed member auth real across devices.

## What this gives you

- Public backend URL for TestFlight and web
- Real shared member accounts instead of device-only accounts
- Persistent SQLite storage on a mounted disk
- Email verification and password reset support

## Files already prepared

- [render.yaml](/C:/temp/Swingle%20Backup/projects/dialed/render.yaml)
- [server/env.example](/C:/temp/Swingle%20Backup/projects/dialed/server/env.example)
- [server/src/database.js](/C:/temp/Swingle%20Backup/projects/dialed/server/src/database.js)
- [server/src/authRoutes.js](/C:/temp/Swingle%20Backup/projects/dialed/server/src/authRoutes.js)

## Render setup

1. Push this repo to GitHub.
2. In Render, create a new Blueprint or Web Service from the repo.
3. Use the included `render.yaml`.
4. Set the missing secret env vars in Render:
   - `APP_URL`
   - `AUTH_RESET_WEB_URL`
   - `AUTH_VERIFICATION_WEB_URL`
   - `SMTP_HOST`
   - `SMTP_USER`
   - `SMTP_PASS`
   - `SMTP_FROM`
   - `OPENAI_API_KEY`
5. Keep `AUTH_DATABASE_PATH=/var/data/dialed.sqlite`.
6. Keep the mounted disk attached so member data survives deploys.

## URL values to use

If Render gives you a backend URL like:

`https://dialed-api.onrender.com`

Then set:

- `APP_URL=https://dialed-api.onrender.com`
- `AUTH_RESET_WEB_URL=https://dialed-api.onrender.com/auth/password/reset`
- `AUTH_VERIFICATION_WEB_URL=https://dialed-api.onrender.com/auth/verify-email`

## App wiring

Once the backend is live, set the app env:

- [C:\temp\Swingle Backup\projects\dialed\.env.example](C:/temp/Swingle%20Backup/projects/dialed/.env.example)

Real value:

`EXPO_PUBLIC_API_BASE_URL=https://dialed-api.onrender.com`

Then rebuild the app so TestFlight points at the hosted backend.

## Sanity checks after deploy

Use these in a browser:

- `/health`
- `/auth/password/reset`
- `/auth/verify-email`

Expected:

- `/health` returns JSON with `ok: true`
- reset page loads
- verification page loads

## Important note

This is a good first production step, but SQLite on a single web service is still a starter architecture. For bigger member volume later, move auth/member storage to Postgres.