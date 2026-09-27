# 1. Architecture

## Application structure

APEX Asset Management is a web application with:

- A React-based frontend.
- A FastAPI/Python backend.
- A database accessed through SQLAlchemy models.
- Docker Compose for containerised deployment.
- Nginx/reverse-proxy infrastructure in the wider APEX environment.
- SMTP integration for account/invitation email.

The asset application is exposed through:

`https://assets.apexingoodcompany.co.uk`

The backend is exposed internally on port `8000` in the current Docker setup.

## Core concepts

### Users

Users have identity, role, active state, location, profile information, authentication data and login/inactivity information.

### Assets

Assets have an automatically generated APEX asset tag such as:

`APEX-000001`

Assets also support QR identification and assignment history.

### Locations

The default operational location is:

`APEX HUB`

### Audit

Administrative and important operational actions are recorded in the audit system.

### Notifications

The platform supports operational alerts including warranty, replacement, maintenance and issue-related attention items, with persistent notifications added in later batches.

## Major feature areas

1. Dashboard and executive management
2. Employee/account management
3. Asset management and lifecycle
4. QR/assignment workflows
5. Maintenance
6. Stock and asset movement
7. Fault/issues
8. Notifications
9. Procurement and suppliers
10. Compliance and documents
11. Finance and expenses
12. Reporting and analytics
13. Profile/settings
14. Security and audit

## Docker

The current backend service is:

`asset-management-backend`

The frontend service is:

`apex-frontend`

Do not remove existing project services or support files when applying an upgrade package.
