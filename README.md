# APEX Asset Management

APEX Asset Management is the central asset inventory and assignment system for APEX.

## Current features

- Automatic asset IDs (`APEX-000001`, `APEX-000002`, ...)
- Unique QR token generated for every asset
- QR code displayed for every asset
- Mobile QR scanner
- Scan a QR code to open an asset
- Assign/reassign an asset to an active user
- Assignment history for every asset
- Audit logging
- User management
- Email invitations with secure 48-hour activation links
- User password activation/login
- Default location: **APEX HUB**
- Asset status, serial number, purchase date, value and category
- User deactivation
- Existing bootstrap admin login remains supported

## Stack

- Backend: FastAPI + SQLAlchemy
- Frontend: React 18 + Axios
- Database: SQLite
- Containers: Docker Compose
- QR scanning: html5-qrcode
- QR generation: qrcode.react

## User invitation flow

An admin goes to **User Management** and enters:

- Full name
- Email
- Phone (optional)
- Role

The location is automatically set to **APEX HUB**.

The system creates a secure invitation token valid for 48 hours and emails the user an activation link. The user chooses a password and can then sign in.

If SMTP is not configured, the API returns a temporary fallback invitation URL to the administrator so the account can still be activated during setup.

## SMTP configuration

Copy `.env.example` to `.env` and set your SMTP details:

```text
APP_PUBLIC_URL=https://assets.apexingoodcompany.co.uk

SMTP_HOST=your.smtp.host
SMTP_PORT=587
SMTP_USERNAME=noreply@apexingoodcompany.co.uk
SMTP_PASSWORD=your-password
SMTP_FROM=noreply@apexingoodcompany.co.uk
SMTP_USE_TLS=true
```

Use the SMTP service you want APEX Asset Management to send mail through (for example, your APEX/OVH/Zimbra mail service).

## QR workflow

1. Admin creates an asset.
2. The system automatically generates its asset ID and QR token.
3. The QR code appears beside the asset.
4. Scan it from a phone.
5. The asset opens in the mobile-friendly asset page.
6. Select a user.
7. Save the assignment.
8. The assignment is added to the asset history and audit log.

QR links use the public Asset Management hostname, so the same QR can be printed and reused throughout the asset's lifetime.

## Docker

```powershell
docker compose up -d --build
```

The existing reverse proxy should continue exposing:

- `https://assets.apexingoodcompany.co.uk`

The backend remains on port 8000 and the frontend on port 3001 on the Docker host.

## Important

The application performs a small startup schema upgrade for existing SQLite databases. Existing assets receive automatic asset IDs and QR tokens, and existing users without a location are assigned **APEX HUB**.
