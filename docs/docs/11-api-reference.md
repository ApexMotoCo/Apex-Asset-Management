# 11. API Reference

This is a functional reference rather than a generated OpenAPI dump. The application's FastAPI `/docs` endpoint should be treated as the authoritative live API reference when enabled.

## Confirmed operational routes from the build

### Health

`GET /health`

Used by the Docker backend healthcheck.

### User

`GET /users/me`

Returns the authenticated user's profile.

`PUT /users/me`

Updates the authenticated user's profile.

`POST /users/me/change-password`

Changes the authenticated user's password.

### Notifications

`GET /notifications`

Returns the user's notification/attention information.

### Assets

`GET /users/me/assets`

Returns assets assigned to the current user.

`POST /assets/import`

Administrator asset import endpoint.

### Maintenance

`GET /maintenance/summary`

Maintenance summary.

`GET /maintenance`

Maintenance records.

`GET /maintenance/{maintenance_id}`

Single maintenance record.

`GET /assets/{asset_id}/maintenance`

Maintenance associated with an asset.

`POST /maintenance`

Create maintenance record.

`PUT /maintenance/{maintenance_id}`

Update maintenance record.

`DELETE /maintenance/{maintenance_id}`

Delete maintenance record.

### Stock

`GET /stock/summary`

Stock summary.

`GET /stock/movements`

Stock movement history.

`POST /assets/{asset_id}/check-out`

Check an asset out.

`POST /assets/{asset_id}/check-in`

Check an asset in.

`POST /assets/bulk-assign`

Bulk assignment.

### Administration

`GET /admin/users`

Administrative user listing.

`GET /admin/settings`

Read system settings.

`PUT /admin/settings`

Update system settings.

### Audit

`GET /audit-logs`

Administrative audit log.

## Live API documentation

FastAPI normally exposes interactive documentation at:

`/docs`

Use the live generated documentation for the exact request/response schemas in the deployed version.
