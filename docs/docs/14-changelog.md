# 14. Release Changelog

## v3.0 — Batches 1–10

### Batch 1 — Core platform

Established the core asset-management application, authentication, asset records, asset IDs, QR identity, assignments and core administration.

### Batch 2 — Lifecycle & reporting

Added asset lifecycle, warranty management, replacement planning, management dashboard, attention reporting, asset profiles, reporting/CSV and expanded audit information.

### Batch 3 — Operations

Added stock/inventory, check-in/check-out, bulk assignment/return, movement history, My Assets, fault/issue reporting, admin issue workflow and expanded attention/notification capabilities.

### Batch 4 — Administration

Added My Profile, password change, System Settings and administrator asset import.

### Batch 5 — Management & automation

Added employee management upgrades, management KPIs, persistent notification capabilities and automated operational alert handling.

### Batch 6 — Procurement

Added suppliers, purchase orders, line items, procurement values and asset-linked purchasing.

### Batch 7 — Compliance

Added asset documents, compliance records, expiry monitoring and compliance dashboard information.

### Batches 8–10 — Final platform expansion

Added finance/expense tracking, budgets, advanced analytics/reporting, executive management information and additional security/system health controls.

### Integration fix

The combined final rebuild initially failed because `Field` was referenced in `schemas.py` without an import. The missing import was added. The corrected package rebuilt successfully and the application returned to normal.

## Current state

The v3.0 cumulative build is operational after the integration fix.

Known item for the next health pass:

- Stock page previously reported as broken and intentionally parked.
