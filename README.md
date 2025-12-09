<h1 align="center">py-LearnStream Platform</h1>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-blue?logo=python&logoColor=white" alt="Python Badge"/>
  <img src="https://img.shields.io/badge/FastAPI-0.110+-green?logo=fastapi&logoColor=white" alt="FastAPI Badge"/>
  <img src="https://img.shields.io/badge/PostgreSQL-SQLAlchemy-blue?logo=postgresql&logoColor=white" alt="PostgreSQL Badge"/>
  <img src="https://img.shields.io/badge/MongoDB-Motor-success?logo=mongodb&logoColor=white" alt="MongoDB Badge"/>
  <img src="https://img.shields.io/badge/Auth-JWT-yellow?logo=jsonwebtokens&logoColor=white" alt="JWT Badge"/>
  <img src="https://img.shields.io/badge/Video-Mux_API-red?logo=mux&logoColor=white" alt="Mux Badge"/>
</p>

---
### Live Deployment

| URL | Description |
|----|-------------|
| 🔗 https://py-learnstream-platform.onrender.com/ | Public landing page |
| 🔗 https://py-learnstream-platform.onrender.com/docs | Swagger UI docs (Full API reference) |

> Backend supports JWT authentication + video asset workflow via Mux.

---

**LearnStream** is a modular, production-grade backend platform for **online learning and secure video delivery**, powered by **FastAPI**, **PostgreSQL**, **MongoDB**, and **Mux API**.

It’s designed to demonstrate a **scalable system architecture** that blends:

* hybrid database patterns (SQL + NoSQL),
* event-driven communication,
* secure JWT-based authentication,
* role-based access control,
* and asynchronous webhooks.

---

## Features

- **JWT Authentication & Role Management**
Stateless auth with refresh tokens and role-based access (Admin, Instructor, Student).

- **Secure Video Lifecycle via Mux API**
Create uploads, receive webhooks, and manage playback securely.

- **Course & Lesson Management**
Create and structure course content with versioning and metadata stored in MongoDB.

- **Student Progress & Analytics Tracking**
Track lesson completion, playback progress, and generate insights.

- **Hybrid Database Architecture**
PostgreSQL for transactional consistency, MongoDB for flexibility and scalability.

- **Asynchronous Webhook Handling**
Fully async FastAPI routes for low latency and concurrency.

- **Scalable Modular Codebase**
Clear separation of concerns and multi-layered architecture for maintainability.

---

## Stack

| Layer | Purpose | Technology |
|-------|----------|------------|
| **API Layer** | Async backend for requests | FastAPI |
| **Relational (CP/EC)** | Authentication, enrollments, payments | PostgreSQL + SQLAlchemy |
| **NoSQL (AP/EL)** | Courses, lessons, analytics, progress | MongoDB + Motor |
| **Caching Layer** | Rate limiting, caching | Redis + aioredis |
| **Streaming API** | Secure video delivery | Mux API |
| **Auth System** | Stateless security | JWT + Passlib |
| **Infrastructure** | Dev and local testing | Docker + Pytest + HTTPX |

---
---

##  Folder Structure

```bash
app/
├── tests/                     # Full testing suite (unit + integration + async) — explained below in detail
│
├── admin/
│   ├── router.py              # Admin-only protected routes (create assets, manage platform resources)
│   └── __init__.py
│
├── auth/
│   ├── router.py              # Endpoints for Login, Register, Logout, Token Refresh
│   ├── deps.py                # FastAPI dependencies: JWT auth, current user extraction, role checking
│   ├── schemas.py             # Request/response validation models (LoginRequest, AuthResponse, etc.)
│   └── __init__.py
│
├── core/
│   ├── config.py              # Global application settings loaded via Pydantic + .env
│   ├── security.py            # Shared security utilities (JWT lifespan, crypto policies)
│   └── __init__.py
│
├── courses/
│   ├── router.py              # Course CRUD endpoints (create, update, list, delete)
│   ├── schemas.py             # Input/output models for Course transport layer
│   └── __init__.py
│
├── lessons/
│   ├── router.py              # Lesson endpoints: metadata, streaming references, Mux asset association
│   ├── schemas.py             # Lesson request/response validation models
│   └── __init__.py
│
├── user/
│   ├── router.py              # User operations: profile update, enrollment request, progress fetch
│   ├── schemas.py             # User schema models (UserOut, UpdateUser, EnrollmentResponse)
│   └── __init__.py
│
├── models/
│   ├── sql/                   # Relational models (PostgreSQL via SQLAlchemy)
│   │   ├── user.py            # User entity: credentials, roles, timestamps (authoritative auth source)
│   │   ├── enrollment.py      # Many-to-many relation: User <-> Course mappings
│   │   ├── refresh_token.py   # Stored hashed refresh tokens for revocation-based session control
│   │   ├── database.py        # Async SQL engine/session + Alembic-ready metadata bindings
│   │   └── __init__.py
│   │
│   ├── nosql/                 # MongoDB async collections (Motor) — AP side of PACELC design
│       ├── course.py          # Course model (dynamic sizing, scalable for content-heavy storage)
│       ├── lesson.py          # Lessons with Mux asset ref → resilient for large datasets
│       ├── progress.py        # Streaming-friendly student progress tracking
│       ├── database.py        # Motor async MongoDB client + collection handlers
│       └── __init__.py
│
├── mux_webhooks/
│   ├── router.py              # Public webhook receiver endpoint for Mux
│   ├── mux_handlers.py        # Event processing: asset.created → asset.ready → lesson binding
│   └── __init__.py
│
├── services/                  # Business logic layer (separate from HTTP layer)
│   ├── mux_service.py         # Mux SDK client: upload URLs, asset creation, signature validation
│   ├── cache_service.py       # Redis caching + rate-limit hooks (future: session cache / predictions)
│   ├── refresh_token_ops.py   # Token rotation, storage, blacklist logic
│   ├── security.py            # Password hashing, JWT encode/decode utilities
│   ├── user_ops.py            # High-level user workflows (signup, update profile, role management)
│   ├── enrollment_ops.py      # Enrollment logic (ensure unique mapping, eligibility, progression)
│   └── utils.py               # (optional) Reusable utility helpers for business workflows
│
├── main.py                    # Application entry — mounts routers, loads config, CORS, middleware
│
├── Dockerfile                 # Deployment image definition (FastAPI + migrations + production server)
├── docker-compose.yml         # Local environment stack: app + Postgres + Mongo (Optional Redis)
├── Makefile                   # Automation commands — serve, format, test, migrate, docker-build
├── render.yml                 # Infrastructure-as-code for Render deployment
├── start.sh                   # Startup script: run alembic migrations → launch server
│
├── alembic.ini                # Alembic migration engine configuration
├── .env.example               # Template environment variables for local development
└── pytest.ini                 # Global pytest settings (async config, test discovery rules)
```

---

##  Database Architecture

The platform implements a **hybrid PACELC-based architecture**, combining the strengths of **CP** and **AP** systems.

<div align="center">
    <img src="./src/pacelc.jpg" alt="pacelc" width="1000" height="550" style="margin-bottom: 1.0em;"/>
</div>

### Design Rationale

- **Consistency-first (CP/EC)** for **authentication**, **payments**, and **user management**, handled by **PostgreSQL**.  
  → Ensures data integrity and secure state transitions.

- **Availability-first (AP/EL)** for **course content**, **progress tracking**, and **analytics**, managed by **MongoDB**.  
  → Optimized for uptime, responsiveness, and scalability.

This architecture ensures users can **always access courses and watch videos** while preserving **strong consistency** where critical.

### Database Structure

```text
SQL (PostgreSQL)
 ├── users
 ├── enrollments
 ├── refresh_tokens
 └── payments (future module)

No-SQL (MongoDB)
 ├── courses
 ├── lessons
 ├── progress
 └── analytics
```

Each Mongo document references SQL user IDs when necessary — maintaining cross-DB consistency while optimizing read/write patterns.

---

## Security and Authentication

The authentication system implements **JWT-based stateless authentication** with **hashed refresh tokens** for revocation support.

| Token Type | Lifetime | Verification                        | Storage    |
| ---------- | -------- | ----------------------------------- | ---------- |
| Access     | Short    | Stateless, verified with secret key | None       |
| Refresh    | Long     | DB-verified (hashed)                | PostgreSQL |



1. **Access Tokens (stateless)**  
   Short-lived; contain user claims and are verified without DB lookup.  
   → Enables horizontal scalability and fast verification.

2. **Refresh Tokens (hashed & stored)**  
   Long-lived; can be revoked by deleting or invalidating their hash.  
   → Provides controlled session management and logout functionality.


---
## Testing

The platform includes a comprehensive test suite covering unit tests, integration tests, and end-to-end scenarios. All tests use **pytest** with **pytest-asyncio** for async support.

### Running Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest app/tests/unit/auth/test_deps.py

# Run specific test
pytest app/tests/unit/auth/test_deps.py::test_get_current_user_valid_token

# Run with coverage
pytest --cov=app --cov-report=html

# Run only unit tests
pytest app/tests/unit/

# Run only integration tests
pytest app/tests/integration/
```

### Test Structure

```
app/tests/
├── conftest.py                    # Shared fixtures and test configuration
├── unit/                          # Unit tests (isolated, mocked dependencies)
│   ├── admin/
│   │   └── test_router_admin.py   # Admin endpoints (uploads, RBAC)
│   ├── auth/
│   │   ├── test_deps.py           # Authentication dependencies (JWT, user extraction)
│   │   └── test_router_auth.py    # Auth routes (login, register, refresh)
│   ├── core/
│   │   └── test_config.py         # Configuration loading and validation
│   ├── courses/
│   │   └── test_router_courses.py # Course management endpoints
│   ├── lessons/
│   │   └── test_router_lessons.py # Lesson playback and access control
│   ├── models/
│   │   ├── sql/                   # SQL model tests (User, Enrollment, etc.)
│   │   └── no_sql/                # MongoDB model tests (Course, Lesson, Progress)
│   ├── mux_webhooks/
│   │   └── test_router_muxwebhook.py  # Mux webhook handling
│   └── services/
│       ├── test_cache_service.py      # Redis caching operations
│       ├── test_mux_services.py       # Mux API integration
│       ├── test_security.py           # JWT and password hashing
│       ├── test_user_ops.py           # User business logic
│       └── test_refresh_token_ops.py  # Refresh token management
└── integration/                   # Integration tests (real DB connections)
    ├── docker-compose.yml        # Test containers setup
    ├── test_end_to_end.py         # Full workflow tests
    └── test_sql_models_integration.py  # SQLAlchemy integration
```

### 1. Unit Tests

**Goal:** Validate isolated logic and internal components, mocking all external dependencies.

#### Authentication Tests (`app/tests/unit/auth/`)

- **`test_deps.py`**: Tests JWT token validation, user extraction, and exception handling
  - Valid token decoding and user retrieval
  - Expired token handling
  - Invalid token handling
  - User not found scenarios
  
- **`test_router_auth.py`**: Tests authentication endpoints
  - User registration
  - Login flow
  - Token refresh
  - Logout functionality

#### Admin Tests (`app/tests/unit/admin/`)

- **`test_router_admin.py`**: Tests admin-only endpoints
  - Role-based access control (RBAC) validation
  - Mux direct upload creation
  - Draft lesson creation
  - Error handling for failed uploads

**Key Testing Pattern:** Mocks are applied at the router import level (e.g., `app.admin.router.create_direct_upload`) to ensure patches work correctly with FastAPI's dependency injection.

#### Lesson Tests (`app/tests/unit/lessons/`)

- **`test_router_lessons.py`**: Tests lesson playback endpoints
  - Lesson retrieval and validation
  - Enrollment verification
  - Mux playback URL generation
  - Access control (403 for non-enrolled users)
  - Missing metadata handling

#### Service Tests (`app/tests/unit/services/`)

- **`test_security.py`**: Password hashing, JWT generation/decoding
- **`test_mux_services.py`**: Mux API client operations
- **`test_cache_service.py`**: Redis caching layer
- **`test_user_ops.py`**: User database operations
- **`test_refresh_token_ops.py`**: Refresh token management

#### Model Tests (`app/tests/unit/models/`)

**SQL Models:**
- User model operations
- Enrollment CRUD
- Refresh token storage

**NoSQL Models:**
- Course document operations
- Lesson document operations
- Progress tracking

| Area                 | Tools                      | Mocked Components                 | Example                                   |
| -------------------- | -------------------------- | --------------------------------- | ----------------------------------------- |
| **Auth**             | `pytest` + `TestClient`    | Mock DB session, JWT decode       | User registration and token rotation      |
| **Admin Uploads**    | `pytest` + `unittest.mock` | Mux upload + Mongo draft lesson   | Verifies upload info is returned          |
| **Lessons**          | `pytest-asyncio`           | Mongo + SQL enrollment data       | Ensures access control + correct playback |
| **Mux Webhooks**     | `HTTPX.AsyncClient`        | Mux signature verification        | Tests valid/invalid event payloads        |
| **CRUD (SQL/Mongo)** | `pytest`                   | Async sessions + fake collections | Ensures inserts, updates, deletes         |

### 2. Integration Tests

**Goal:** Validate interaction between modules and databases under real conditions.

Built using **Docker Compose** with PostgreSQL, MongoDB, Redis test containers and **pytest-asyncio** + **HTTPX.AsyncClient** for async tests.

Each integration test launches the full FastAPI app with test containers and simulates end-to-end flows:

* User registration → course enrollment → lesson playback
* Admin uploads → Mux webhook triggers → lesson state update

**Running Integration Tests:**
```bash
# Start test containers
cd app/tests/integration
docker-compose up -d

# Run integration tests
pytest app/tests/integration/

# Cleanup
docker-compose down
```

### 3. Test Fixtures & Utilities

`conftest.py` defines reusable fixtures and utilities:

**Fixtures:**
- `client`: FastAPI `TestClient` for synchronous HTTP requests
- `mock_auth`: Automatically mocks authentication for all tests
- `override_get_current_user`: Global authentication override for test isolation

**Utilities:**
- `FakeResult`: Mock SQLAlchemy result object for testing database queries
- Dependency overrides for FastAPI's dependency injection system

**Testing Patterns:**

1. **Mocking at Import Level**: Functions are patched where they're imported (e.g., `app.admin.router.create_direct_upload`) rather than where they're defined, ensuring FastAPI's dependency injection works correctly.

2. **Dependency Overrides**: FastAPI's `app.dependency_overrides` is used to replace authentication and database dependencies in tests.

3. **Async Testing**: All async functions are tested using `pytest.mark.asyncio` and `AsyncMock` from `unittest.mock`.

4. **Isolated Test Logic**: For complex dependencies (like `get_current_user` with `Depends(oauth2_scheme)`), tests replicate the core logic directly to avoid dependency injection complications.

### Test Coverage

The test suite covers:
-  Authentication and authorization flows
-  Admin operations (uploads, RBAC)
-  Course and lesson management
-  Mux API integration
-  Database operations (SQL and NoSQL)
-  Service layer business logic
-  Error handling and edge cases

**Note:** Integration tests require Docker and test containers. Ensure Docker is running before executing integration test suites.

---

## Admin Uploads

Admins can upload video assets via:
```
POST /admin/uploads
````
This endpoint integrates directly with the **Mux API** to create upload URLs.  
It returns signed upload information, allowing frontends or other services to upload videos securely and track their status.

---

## Webhooks

### Mux Webhook (`/webhooks/mux`)

Handles asynchronous video lifecycle events from Mux — such as:
- `video.asset.created`
- `video.asset.ready`
- `video.upload.cancelled`
- `video.asset.errored`

Each event is verified for authenticity using **Mux signature headers** and logged with contextual data for debugging and analytics.



#### Registering the Webhook in Mux Dashboard

1. Log in to [https://dashboard.mux.com](https://dashboard.mux.com)
2. Go to **Settings → Webhooks**
3. Click **+ Create Webhook**
4. Choose environment (**Production** or **Development**)
5. Enter your ngrok/public URL + `/webhooks/mux`
6. Select event types (e.g. *video.asset.created*, *video.asset.ready*)
7. Save — you’ll receive a **Signing Secret**
8. Add to `.env` file as:

   MUX_WEBHOOK_SECRET=your_signing_secret


---

##  Author

**Adan Siqueira**  
🔗 [GitHub Profile](https://github.com/AdanSiqueira)

---

If you like this project, don’t forget to ⭐ **star the repository** to show your support!