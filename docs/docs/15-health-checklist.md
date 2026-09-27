# 15. v3.0 Health Checklist

Use this after every major deployment.

## Infrastructure

- [ ] Docker Compose starts
- [ ] Backend container is running
- [ ] Frontend container is running
- [ ] Backend healthcheck passes
- [ ] No startup traceback in backend logs

## Authentication

- [ ] Login works
- [ ] Admin login works
- [ ] Normal user access works
- [ ] Password change works
- [ ] User invitation works

## Core assets

- [ ] Asset list loads
- [ ] Asset creation works
- [ ] Asset profile loads
- [ ] QR workflow works
- [ ] Assignment works
- [ ] Check-in works
- [ ] Check-out works
- [ ] Asset history loads

## Operations

- [ ] Maintenance loads
- [ ] Issues load
- [ ] Stock loads
- [ ] Notifications load
- [ ] My Assets loads

## Management

- [ ] Executive/Management dashboard loads
- [ ] Employees loads
- [ ] Procurement loads
- [ ] Compliance loads
- [ ] Finance loads
- [ ] Reports/analytics load

## Administration

- [ ] Profile loads
- [ ] Settings loads
- [ ] Admin Users loads
- [ ] Audit Logs load

## Security

- [ ] No secrets appear in Git
- [ ] Admin routes reject ordinary users
- [ ] Inactive-account rules behave as configured
- [ ] Audit entries are created for administrative actions

## Data

- [ ] Database backup completed
- [ ] Existing assets still present
- [ ] Existing users still present
- [ ] Assignments still present
- [ ] No unexpected duplicate asset IDs
