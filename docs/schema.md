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
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE,
    deleted_at TIMESTAMP WITH TIME ZONE
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

### System Fields
- `created_at`: Timestamp of creation
- `updated_at`: Timestamp of last update
- `deleted_at`: Soft deletion timestamp