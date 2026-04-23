# Member Auth Rollout

Dialed now has a real backend member-auth foundation for live users.

## What is in place

- `POST /api/auth/register`
- `POST /api/auth/login`
- `POST /api/auth/logout`
- `GET /api/auth/me`
- `POST /api/auth/email/resend-verification`
- `GET /auth/verify-email` for email verification links
- `PATCH /api/auth/subscription`
- `PATCH /api/auth/profile`
- `POST /api/auth/password/change`
- `POST /api/auth/password/request-reset`
- `POST /api/auth/password/reset`
- `GET /auth/password/reset` for email-link password resets
- `GET /api/admin/members`
- `PATCH /api/admin/members/:memberId`
- `POST /api/admin/members/:memberId/reset-password`
- `POST /api/admin/members/:memberId/resend-verification`
- `POST /api/admin/members/:memberId/force-logout`

Server files:

- [server/src/database.js](/C:/temp/Swingle%20Backup/projects/dialed/server/src/database.js)
- [server/src/emailService.js](/C:/temp/Swingle%20Backup/projects/dialed/server/src/emailService.js)
- [server/src/authRoutes.js](/C:/temp/Swingle%20Backup/projects/dialed/server/src/authRoutes.js)
- [server/src/memberAuthStore.js](/C:/temp/Swingle%20Backup/projects/dialed/server/src/memberAuthStore.js)

## Security posture today

- Member passwords are hashed with Node `scrypt`.
- Sessions use server-side random tokens.
- Password reset uses time-limited reset tokens.
- Email verification uses time-limited verification tokens.
- Member auth now persists to SQLite in `server/data/dialed.sqlite` by default.
- Legacy JSON auth data is imported into SQLite on first run if the database is empty.
- Duplicate emails are blocked server-side.
- Password reset and password change clear reset tokens, and reset clears all active sessions.
- Password reset also marks the email as verified.
- Admin routes are restricted to the configured admin email.

## Environment you still need to set

- `APP_URL`
- `AUTH_RESET_WEB_URL`
- `AUTH_VERIFICATION_WEB_URL`
- `SMTP_HOST`
- `SMTP_PORT`
- `SMTP_SECURE`
- `SMTP_USER`
- `SMTP_PASS`
- `SMTP_FROM`
- `ADMIN_EMAIL`

## What still needs to happen before real production launch

1. Move SQLite from a local server file to a managed production database service.
2. Point SMTP at a real provider and verify the sender domain.
3. Deploy the backend to a public URL and point `EXPO_PUBLIC_API_BASE_URL` at it so phone builds stop falling back to local-only auth.
4. Add payment and subscription billing with Stripe or RevenueCat.
5. Add abuse protection and rate limiting on auth routes.
6. Move workout/member data fully server-side and enforce ownership checks across every protected API.
7. Add admin audit history and support notes so interventions are fully traceable.

## Development note

`AUTH_EXPOSE_RESET_TOKENS=true` leaves reset tokens, reset links, and verification links visible in API responses for development. Set it to `false` before production and rely on email delivery instead.

## Admin note

`ADMIN_EMAIL` controls who can access the admin portal and admin routes. The default is `frederick.swingle@westpoint.edu`.