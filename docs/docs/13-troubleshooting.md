# 13. Troubleshooting

## Backend will not start

Run:

```powershell
docker logs asset-management-backend --tail 200
```

Look for the first Python traceback and the final exception.

Do not assume a frontend error is a frontend problem: if the backend container is failing to import, multiple pages can fail simultaneously.

## Frontend says "Unable to load..."

Check backend health first:

```powershell
docker compose ps
docker logs asset-management-backend --tail 100
```

If several unrelated pages fail at once, inspect the backend before changing React components.

## Backend syntax/import error

Typical workflow:

1. Capture the complete traceback.
2. Identify the file and line.
3. Fix the import/model/schema issue.
4. Run Python compilation checks.
5. Rebuild.
6. Check startup logs again.

## Docker rebuild

```powershell
docker compose down
docker compose up -d --build
```

## Container status

```powershell
docker compose ps
```

## Stock page

The Stock page has previously been reported as broken. If it still fails:

```powershell
docker logs asset-management-backend --tail 200
```

Then inspect the browser/network error for the failing Stock endpoint. Do not guess at the cause.

## Database problems

Check:

- Active `DATABASE_URL`
- Database file path
- Container volume
- Schema/table existence
- Startup logs

Take a backup before repair work.

## Email problems

Verify:

- SMTP host
- SMTP port
- TLS setting
- SMTP username
- Sender address
- SMTP password/secret
- Container environment

Never paste the SMTP password into chat or Git.
