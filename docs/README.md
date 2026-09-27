# APEX Asset Management — Documentation

**Release baseline:** v3.0  
**Scope:** Batches 1–10, including the Batch 8–10 integration fix.

This documentation describes the APEX Asset Management platform as built through the ten planned upgrade batches. It is intended for administrators, maintainers and future developers.

## Documentation map

- [Architecture](docs/01-architecture.md)
- [Deployment & Updates](docs/02-deployment.md)
- [Administration Guide](docs/03-administration.md)
- [Assets & Lifecycle](docs/04-assets-and-lifecycle.md)
- [Maintenance, Issues & Stock](docs/05-maintenance-issues-stock.md)
- [Employees, Accounts & Notifications](docs/06-users-and-notifications.md)
- [Procurement & Suppliers](docs/07-procurement.md)
- [Compliance & Documents](docs/08-compliance-and-documents.md)
- [Finance & Reporting](docs/09-finance-and-reporting.md)
- [Security & Audit](docs/10-security-and-audit.md)
- [API Reference](docs/11-api-reference.md)
- [Backup & Recovery](docs/12-backup-and-recovery.md)
- [Troubleshooting](docs/13-troubleshooting.md)
- [Release Changelog](docs/14-changelog.md)

## Important implementation note

The application has been developed in cumulative batches. Batches 1–10 were ultimately combined and rebuilt together. A Batch 8–10 startup problem was found during integration: `schemas.py` used `Field` without importing it. The import was added and the combined package was rebuilt. The backend subsequently returned to normal operation.

## Known parked item

The Stock page previously showed a problem during Batch 3. It was deliberately parked while the remaining platform work was completed. It should be included in the next formal health pass rather than silently considered fixed.
