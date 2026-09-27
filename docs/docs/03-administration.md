# 3. Administration Guide

## Admin areas

The application includes administrative areas for:

- Employees/users
- Assets
- Maintenance
- Issues
- Stock
- Procurement
- Compliance
- Finance
- Reports
- Notifications
- System settings
- Audit logs
- Executive/management reporting

## System Settings

System settings introduced in the later upgrade work include:

- Organisation name
- Default location
- User inactivity period
- Maintenance due-soon period

The initial defaults include:

- Organisation: `APEX`
- Default location: `APEX HUB`
- User inactivity: `30` days
- Maintenance due-soon: `14` days

Existing values should not be overwritten automatically when the application starts.

## User inactivity

The inactivity setting is configurable from administration settings and is used by the application's inactivity enforcement.

## Profile

Users can update:

- Full name
- Phone
- Bio
- Location

Users can also change their password. Password changes require the current password and a new password meeting the configured minimum validation.

## Asset import

The application includes an administrator asset import capability. The backend import accepts structured rows and creates asset records, assigns asset tags and QR tokens, and reports created/skipped/error results.

Before large imports, take a database backup.
