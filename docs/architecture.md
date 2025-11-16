# User Service Architecture

## Overview
User Service is a Django REST Framework-based microservice that manages extended user profiles.  
It works in conjunction with the auth-service, which is responsible for authentication and authorization.  
This service is designed for a high-load ticket booking system and focuses on scalability, robustness, and clean separation of concerns.

---

## Current Components

### Models
- **UserProfile**
  - Stores extended user information linked to auth-service via `auth_id`
  - Core fields:
    - Identification: `id` (UUID), `auth_id`, `email`, `username`
    - Personal data: `first_name`, `last_name`, `phone`, `date_of_birth`, `gender`, `address` (JSON)
    - Lifecycle: `created_at`, `updated_at`, `deleted_at` (soft delete)
  - Email verification fields:
    - `is_email_verified` — boolean flag indicating verified email
    - `email_verification_code` — one-time verification code
    - `email_verification_expires_at` — expiration timestamp
    - `email_verification_sent_at` — when the code was last sent
  - Utility methods:
    - `soft_delete()` — marks record as deleted without physical removal
    - `generate_email_verification_code()` — generates and persists a time-limited verification code

### API Layer
- **Framework**: Django REST Framework
- **Endpoints**:
  - Profile management:
    - `GET /api/v1/profiles/` — list profiles (with optional filtering by `auth_id`)
    - `GET /api/v1/profiles/{id}/` — retrieve a specific profile
    - `POST /api/v1/profiles/` — create profile
    - `PUT /api/v1/profiles/{id}/` — full update
    - `PATCH /api/v1/profiles/{id}/` — partial update
    - `DELETE /api/v1/profiles/{id}/` — soft delete
  - Email verification:
    - `POST /api/v1/profiles/{id}/send-email-verification/` — enqueue background task to send verification code
    - `POST /api/v1/profiles/{id}/verify-email/` — validate code and mark email as verified
- **Documentation**:
  - Swagger / OpenAPI via `drf_yasg` (`/swagger`, `/redoc`)
- **Admin UI**:
  - Customized Django Admin using **Unfold** for better UX when managing profiles

### Storage
- **PostgreSQL**
  - Primary relational database
  - Single-table architecture for user profiles (`user_profiles`)
  - Indexed fields:
    - `auth_id`
    - `email`
  - Supports soft deletion via `deleted_at` field (records remain in DB but are excluded from default queries)

### Caching
- **Redis** as cache backend
  - Used for:
    - Caching individual profile responses by `id` and `auth_id`
    - Caching profile list results
  - Reduces load on PostgreSQL and improves response times for frequently accessed data
  - Cache is invalidated on create/update/delete operations through helper methods inside the ViewSet

### Background Processing
- **Celery**
  - Runs as a separate worker process/container
  - Uses Redis as broker and result backend
  - Current tasks:
    - `send_email_verification_task`:
      - Loads `UserProfile` by ID
      - Calls `generate_email_verification_code()` on the model
      - Sends verification email with the generated code
      - Implements retries and logging
  - Decouples slow operations (like email sending) from the HTTP request/response cycle

### Email Delivery
- **Django Email Backend**
  - Pluggable configuration via environment variables (`EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, etc.)
  - Development mode can use console backend (logs messages instead of real sending)
  - Production mode uses SMTP (e.g. Gmail, corporate SMTP) to deliver real email verification codes

### Admin Interface
- **Django Admin + Unfold**
  - Management of user profiles
  - Enhanced UX/theme via Unfold configuration
  - Suitable for internal support and operations staff

---

## Implementation Details

### Authentication & Integration
- The service does **not** authenticate users directly; instead:
  - Relies on **auth-service** for authentication and JWT issuance
  - Uses `auth_id` as a foreign key-like reference to the auth-service user
- `AUTH_SERVICE_URL` is configurable via environment variables to allow different deployments (dev/stage/prod)

### Data Management
- **Soft deletion**
  - `deleted_at` indicates logical deletion
  - Default queryset excludes deleted records
  - `soft_delete()` encapsulates deletion semantics in the model
- **Timestamps**
  - `created_at` set on creation
  - `updated_at` auto-updated on each save
- **Uniqueness**
  - `auth_id`, `email`, and `phone` (if provided) are unique
  - Ensures consistent mapping between auth-service and user-service profiles
- **Email verification logic**
  - Verification code is numeric and time-limited
  - Verification flow:
    1. Client calls `send-email-verification` → Celery task enqueued
    2. Code is generated and stored in the profile with expiry timestamp
    3. Email is sent to the user with the code
    4. Client calls `verify-email` with the code
    5. Service validates the code, expiry, and marks `is_email_verified = True` on success

### Caching Strategy
- **Key patterns**:
  - `user_profile_{profile_id}` — cached profile by UUID
  - `user_profile_auth_{auth_id}` — cached profile(s) by auth-service ID
  - `user_profiles_list_all` — cached list of all profiles (for admin use cases)
- **Invalidation**:
  - On create/update/delete:
    - Profile-specific keys are removed
    - Global list cache is invalidated
- **Backend**:
  - `django_redis` with connection pooling and timeouts

### Logging & Observability
- **Django Logging**
  - File and console handlers configured
  - Logs application events, profile updates, deletions
- **Request Logging Middleware**
  - Custom middleware in `users.middleware.RequestLoggingMiddleware`
  - Captures incoming requests and useful metadata for debugging and auditing
- **Celery Logging**
  - Logs task execution, retries, and failures for background jobs

### Environment & Deployment
- **Docker-based**
  - Separate containers for:
    - Web (Django + DRF)
    - Database (PostgreSQL)
    - Cache/Broker (Redis)
    - Celery worker
  - `docker compose` orchestrates the stack
- **Configuration via Environment Variables**
  - Core:
    - `DEBUG`, `SECRET_KEY`, `ALLOWED_HOSTS`, `TIME_ZONE`
  - Database:
    - `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`
  - Redis:
    - `REDIS_HOST`, `REDIS_PORT`, `REDIS_PASSWORD`
  - Celery:
    - `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`
  - Email:
    - `EMAIL_BACKEND`, `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `DEFAULT_FROM_EMAIL`
  - Integration:
    - `AUTH_SERVICE_URL`
  - Documentation:
    - `SWAGGER_PUBLIC` flag to toggle schema visibility

---

## Summary
User Service encapsulates extended user profile management for the ticket booking platform.  
With Redis-based caching, Celery-driven background email verification, and a clean REST API, it is designed to be scalable, maintainable, and ready to integrate with other microservices (auth, booking, events, notifications).
