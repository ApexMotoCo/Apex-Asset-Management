# 2. Deployment & Updates

## Current Windows/Docker environment

Project:

`C:\Users\Adam\Documents\GitHub\Apex-Asset-Management`

The application is deployed with Docker Compose.

## Standard rebuild

From PowerShell:

```powershell
cd "C:\Users\Adam\Documents\GitHub\Apex-Asset-Management"
docker compose down
docker compose up -d --build
```

Then check:

```powershell
docker compose ps
```

## Backend diagnostics

```powershell
docker logs asset-management-backend --tail 100
```

For a larger diagnostic window:

```powershell
docker logs asset-management-backend --tail 300
```

## Update procedure

1. Back up the database.
2. Check Git status.
3. Pull or apply the intended changes.
4. Review changed files.
5. Rebuild Docker.
6. Check container status.
7. Check backend logs.
8. Log into the web application.
9. Run the health checklist.
10. Commit and push only after verification.

## Do not

- Delete unrelated backend modules such as authentication, audit or database configuration files.
- Replace the whole project with an upgrade ZIP unless the package explicitly contains the complete project.
- Assume a successful Docker build means every API endpoint works.
- Skip database backups before schema-changing upgrades.
