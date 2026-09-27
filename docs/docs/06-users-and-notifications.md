# 6. Employees, Accounts & Notifications

## Employee management

Employee/user management supports:

- User profiles
- Active/inactive status
- Roles
- Locations
- Last login
- Assigned asset visibility
- Administrative account controls

## Invitation flow

The system supports invited-user onboarding and invitation email delivery through SMTP.

The verified SMTP configuration used during development was:

- SMTP host: `smtp.mail.ovh.net`
- SMTP port: `587`
- TLS enabled
- Sender: `business@apexingoodcompany.co.uk`

Secrets/passwords must remain in environment configuration and must never be committed to Git.

## Notifications

Notification functionality covers:

- Warranty alerts
- Replacement alerts
- Maintenance alerts
- Issue/fault alerts
- Attention items
- Read/unread state
- Mark-as-read
- Mark-all-as-read

## My Assets

Users can view assets currently assigned to them.

## Account security

Deactivation and inactivity controls should be used instead of deleting users where historical assignment/audit records need to remain meaningful.
