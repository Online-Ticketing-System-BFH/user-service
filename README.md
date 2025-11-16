# User Service API - High-Load Ticket Booking System

**Extended User Profile Management**

A scalable, high-performance user profile service API built with Django REST Framework. This service manages extended user information and integrates with the auth-service for authentication. Part of the high-load ticket booking system microservices architecture.

### Prerequisites

- Docker & Docker Compose installed
- Python 3.11+
- PostgreSQL
- Redis (for caching)

### Start the Service

```bash
# Clone/navigate to project directory
cd user-service

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Linux/MacOS
.\venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Start everything (API + Database)
docker compose up --build

# Or run in background
docker compose up -d
```

**That's it!** The service is now running at:
- 🌐 **API**: http://localhost:8000/api/v1
- 📚 **Interactive Docs**: http://localhost:8000/swagger
- 📖 **Alternative Docs**: http://localhost:8000/redoc
- 🔐 **Admin Panel**: http://localhost:8000/admin

### Quick API Test

```bash
# Check health
curl http://localhost:8000/api/v1/healthz
```
---

## 📊 Features

### Core Functionality

✅ **Extended Profiles**: Store additional user information beyond auth data
✅ **Email Verification**: Background email confirmation using Celery task workers
✅ **Admin Management**: Enhanced admin interface with Unfold
✅ **Profile Updates**: Update personal information and preferences
✅ **Soft Deletion**: Non-destructive profile removal
✅ **Activity Tracking**: Monitor user profile changes and updates

### Technical Features

#### Security & Integration
- User data protection
- Cross-service communication
- Integration with auth-service for user verification
- Ready for event and booking service integration

#### Performance Optimization
- Profile data caching with Redis
- Optimized database queries
- Bulk operations support
- Efficient soft deletions
- Response compression
- Connection pooling

#### Background Tasks
- Email verification handled by Celery workers
- Automatic retries for failed email delivery

#### Developer Experience
- Comprehensive API documentation
- Interactive Swagger UI
- Clear error messages
- Request/Response logging
- Development environment setup

---

## 🔗 API Endpoints

### Profile Management
- `GET /api/v1/profiles/` - List all profiles (admin only)
- `GET /api/v1/profiles/{id}/` - Get specific profile
- `DELETE /api/v1/profiles/{id}/` - Soft delete profile

### Email Verification
- `POST /api/v1/profiles/{id}/send-email-verification/` — send verification code to user's email
- `POST /api/v1/profiles/{id}/verify-email/` — verify email using the received code

### 1. Send Verification Code
`POST /api/v1/profiles/{id}/send-email-verification/`

### 2. Verify Email Code
`POST /api/v1/profiles/{id}/verify-email/`
```http
{
  "code": "123456"
}
```

### Response Examples

#### Get Profile Response
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "auth_id": 12345,
  "email": "user@example.com",
  "username": "john_doe",
  "first_name": "John",
  "last_name": "Doe",
  "full_name": "John Doe",
  "phone": "+77001234567",
  "date_of_birth": "1990-01-01",
  "gender": "M",
  "address": {
    "city": "Almaty",
    "street": "Abai Avenue",
    "building": "150",
    "postal_code": "050000"
  },
  "created_at": "2025-10-15T10:30:00Z",
  "updated_at": "2025-10-15T10:30:00Z"
}
```

---

## 🛠 Development

### Environment Variables

The service uses the following environment variables. Create a `.env` file with:

```ini
# ===== Core =====
# Debug-режим: False для продакшена
DEBUG=False
# Сгенерируй длинный случайный ключ (40–100+ символов)
SECRET_KEY="CHANGE_ME_SUPER_SECRET_KEY"

# Через запятую, без пробелов
ALLOWED_HOSTS=localhost,127.0.0.1

# Разрешённые источники CORS/CSRF (через запятую)
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
CSRF_TRUSTED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
CORS_ALLOW_CREDENTIALS=True

# Часовой пояс
TIME_ZONE=Asia/Almaty


# ===== Database =====
DB_NAME=user_service_db
DB_USER=postgres
DB_PASSWORD="CHANGE_ME_DB_PASSWORD"
DB_HOST=db
DB_PORT=5432


# ===== Redis =====
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD="CHANGE_ME_REDIS_PASSWORD"


# ===== JWT =====
# Используй очень длинный секрет (64+ байт)
JWT_SECRET_KEY="CHANGE_ME_LONG_JWT_SECRET"
JWT_ALGORITHM=HS256


# ===== External Services =====
AUTH_SERVICE_URL=http://auth-service:5000


# ===== Celery =====
# Если в пароле есть спецсимволы, оставляй в кавычках
# Формат: redis://:PASSWORD@HOST:PORT/DB_INDEX
CELERY_BROKER_URL="redis://:CHANGE_ME_REDIS_PASSWORD@redis:6379/0"
CELERY_RESULT_BACKEND="redis://:CHANGE_ME_REDIS_PASSWORD@redis:6379/0"


# ===== Swagger / Docs =====
# True — публичная схема, False — доступ по аутентификации
SWAGGER_PUBLIC=True
```

### Database Migrations

```bash
# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate
```


---

## 📚 Documentation

- Full API documentation available at `/swagger` or `/redoc`
- Architecture details in `docs/architecture.md`
- Database schema in `docs/schema.md`

---

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.