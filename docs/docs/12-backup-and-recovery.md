# 12. Backup & Recovery

## Database

The application has used SQLite during development. The exact active database path is controlled by the deployment configuration and should not be assumed from older backups.

Before schema-changing work, back up the active database from the running container.

Example pattern:

```powershell
docker cp asset-management-backend:/app/assets.db .\backups\assets-backup-YYYY-MM-DD.db
```

If the deployment has moved the database to `/data/assets.db`, use that active path instead.

## Recovery principle

1. Stop the application if required.
2. Identify the active database location.
3. Preserve the damaged database before replacing anything.
4. Restore the verified backup.
5. Start the backend.
6. Check logs.
7. Verify users/assets/assignments.
8. Check audit records.
9. Test login and key workflows.

## Important

Do not overwrite a production database without first making a copy of the current state.

## Existing development backup

A backup was created during development before the QR/user work:

`backups\assets-before-qr-users-2026-09-26.db`

This is historical and must not automatically be treated as the current production backup.
