# Database Schema

## UserProfile Table

Current implementation of the user profile storage.

```sql
CREATE TABLE user_profiles (
    id UUID PRIMARY KEY,
    auth_id INTEGER UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(50) NOT NULL,

    first_name VARCHAR(100),
    last_name VARCHAR(100),
    phone VARCHAR(20) UNIQUE,
    date_of_birth DATE,
    gender VARCHAR(1),
    address JSONB,

    is_email_verified BOOLEAN NOT NULL DEFAULT FALSE,
    email_verification_code VARCHAR(6),
    email_verification_expires_at TIMESTAMPTZ,
    email_verification_sent_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ,
    deleted_at TIMESTAMPTZ
);

```

## Field Descriptions

### Required Fields
- `id`: UUID, primary key
- `auth_id`: Integer, links to auth-service user
- `email`: String, unique user email
- `username`: String, user's username

### Optional Fields
- `first_name`: String
- `last_name`: String
- `phone`: String, unique when provided
- `date_of_birth`: Date
- `gender`: Single character (M/F)
- `address`: JSON object

### Email Verification Fields
- `is_email_verified` — boolean (default false)
- `email_verification_code` — 6-digit code
- `email_verification_expires_at` — code validity timestamp
- `email_verification_sent_at` — when code was generated

### System Fields
- `created_at`: Timestamp of creation
- `updated_at`: Timestamp of last update
- `deleted_at`: Soft deletion timestamp