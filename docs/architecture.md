# User Service Architecture

## Overview
User Service is a Django REST Framework-based service that manages extended user profiles. It works in conjunction with the auth-service, which handles authentication and authorization.

## Current Components

### Models
- UserProfile - stores extended user information
- Integration with auth-service via auth_id

### API Layer
- Django REST Framework
- Basic CRUD operations for user profiles

### Storage
- PostgreSQL database
- Single table architecture
- Soft deletion support

### Admin Interface
- Django Admin interface
- User profile management
- Basic CRUD operations

## Implementation Details

### Authentication
- Integration with auth-service

### Data Management
- Soft deletion (deleted_at field)
- Created/Updated timestamps
- Unique constraints on critical fields

### Environment
- Docker containerization
- Environment variable configuration
- Django's built-in logging