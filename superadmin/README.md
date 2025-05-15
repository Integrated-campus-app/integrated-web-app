# Super Admin System

This module provides a comprehensive backend system for managing administrative roles and workflows within the university web application.

## Features

- Department Management
- Admin User Management
- Issue Tracking and Resolution
- Audit Logging
- System Metrics and Performance Tracking
- Role-based Access Control

## API Endpoints

### Departments

- `GET /api/superadmin/departments/` - List all departments
- `POST /api/superadmin/departments/` - Create a new department
- `GET /api/superadmin/departments/{id}/` - Get department details
- `PUT /api/superadmin/departments/{id}/` - Update department
- `DELETE /api/superadmin/departments/{id}/` - Delete department
- `GET /api/superadmin/departments/{id}/metrics/` - Get department metrics

### Admin Users

- `GET /api/superadmin/admins/` - List all admin users
- `POST /api/superadmin/admins/` - Create a new admin user
- `GET /api/superadmin/admins/{id}/` - Get admin details
- `PUT /api/superadmin/admins/{id}/` - Update admin
- `DELETE /api/superadmin/admins/{id}/` - Delete admin
- `POST /api/superadmin/admins/{id}/deactivate/` - Deactivate admin
- `POST /api/superadmin/admins/{id}/activate/` - Activate admin

### Issues

- `GET /api/superadmin/issues/` - List all issues
- `POST /api/superadmin/issues/` - Create a new issue
- `GET /api/superadmin/issues/{id}/` - Get issue details
- `PUT /api/superadmin/issues/{id}/` - Update issue
- `DELETE /api/superadmin/issues/{id}/` - Delete issue
- `POST /api/superadmin/issues/{id}/assign/` - Assign issue to admin
- `POST /api/superadmin/issues/{id}/resolve/` - Resolve issue

### Audit Logs

- `GET /api/superadmin/audit-logs/` - List all audit logs
- `GET /api/superadmin/audit-logs/{id}/` - Get audit log details

### System Metrics

- `GET /api/superadmin/metrics/` - List all metrics
- `GET /api/superadmin/metrics/dashboard/` - Get dashboard metrics

## Authentication

All endpoints require JWT authentication. Include the token in the Authorization header:

```
Authorization: Bearer <your_token>
```

## Permissions

- Super Admin: Full access to all endpoints
- Department Admin: Access to their department's issues and metrics

## Models

### Department

- name (CharField)
- code (CharField)
- description (TextField)
- is_active (BooleanField)
- created_at (DateTimeField)
- updated_at (DateTimeField)

### AdminProfile

- user (OneToOneField to User)
- departments (ManyToManyField to Department)
- is_active (BooleanField)
- last_active (DateTimeField)
- created_at (DateTimeField)
- updated_at (DateTimeField)

### Issue

- title (CharField)
- description (TextField)
- department (ForeignKey to Department)
- reported_by (ForeignKey to User)
- assigned_to (ForeignKey to AdminProfile)
- status (CharField)
- urgency (CharField)
- resolution_notes (TextField)
- created_at (DateTimeField)
- updated_at (DateTimeField)
- resolved_at (DateTimeField)

### AuditLog

- user (ForeignKey to User)
- action (CharField)
- model_name (CharField)
- object_id (IntegerField)
- details (JSONField)
- timestamp (DateTimeField)

### SystemMetrics

- department (ForeignKey to Department)
- date (DateField)
- new_issues (IntegerField)
- resolved_issues (IntegerField)
- avg_resolution_time (FloatField)

## Usage Examples

### Creating a Department

```python
POST /api/superadmin/departments/
{
    "name": "Computer Science",
    "code": "CS",
    "description": "Department of Computer Science"
}
```

### Creating an Admin User

```python
POST /api/superadmin/admins/
{
    "user": {
        "username": "csadmin",
        "email": "csadmin@university.edu",
        "first_name": "John",
        "last_name": "Doe"
    },
    "department_ids": [1, 2]
}
```

### Creating an Issue

```python
POST /api/superadmin/issues/
{
    "title": "System Downtime",
    "description": "Main server is not responding",
    "department": 1,
    "urgency": "high"
}
```

### Assigning an Issue

```python
POST /api/superadmin/issues/1/assign/
{
    "admin_id": 1
}
```

### Resolving an Issue

```python
POST /api/superadmin/issues/1/resolve/
{
    "resolution_notes": "Server restarted and running normally"
}
```

## Error Handling

The API uses standard HTTP status codes and returns error messages in the following format:

```json
{
  "error": "Error message",
  "details": {
    "field_name": ["Error description"]
  }
}
```

## Rate Limiting

API endpoints are rate-limited to prevent abuse. The current limits are:

- 100 requests per minute for authenticated users
- 20 requests per minute for unauthenticated users

## Caching

Some endpoints (like audit logs and metrics) are cached to improve performance. Cache duration is 1 minute by default.
