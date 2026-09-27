# 10. Security & Audit

## Authentication

The application uses authenticated sessions/tokens and role-based access controls.

Administrative operations are restricted to appropriate roles.

## Passwords

Passwords are stored as hashes rather than plaintext.

Password changes require verification of the current password.

## Roles

The system distinguishes ordinary members/users from administrative roles, with elevated controls for administrators and super-admin functionality.

## Inactivity

User inactivity is configurable. Inactive accounts should be reviewed before reactivation.

## Audit log

Audit logging records important administrative and operational actions.

Examples include:

- Asset actions
- User/admin actions
- Maintenance changes
- Procurement changes
- Compliance changes
- Document changes
- Settings changes
- Password/security actions

## Security rules

Never commit:

- SMTP passwords
- Secret keys
- JWT secrets
- API tokens
- Database passwords
- Private certificates
- VPN private keys

Use environment variables or protected deployment secrets.

## Final integration fix

During the combined Batch 8–10 rebuild, the backend failed because `schemas.py` referenced `Field` without importing it. The missing import was added and the backend returned to normal. This is documented as an integration lesson: syntax checking individual files is not sufficient; the full application must be imported and started after a cumulative upgrade.
