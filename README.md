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
## Testing (working on it)

### 1. Unit Tests

**Goal:** Validate isolated logic and internal components, mocking all external dependencies.

| Area                 | Tools                      | Mocked Components                 | Example                                   |
| -------------------- | -------------------------- | --------------------------------- | ----------------------------------------- |
| **Auth**             | `pytest` + `TestClient`    | Mock DB session                   | User registration and token rotation      |
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

### 3. Fixtures & Utilities

`conftest.py` defines reusable fixtures:

* `client` / `async_client`: FastAPI test client (sync/async)
* `mock_db_session`: Fake SQLAlchemy session (in-memory)
* `mock_mongo`: Fake Motor client using `mongomock`
* `mock_mux_service`: Patch `create_direct_upload()` and related Mux API calls
* `admin_token` / `student_token`: Prebuilt JWTs for different roles
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

## 🧾 Folder Structure

```bash
app/
├── admin/
│   ├── router.py              # Admin-only endpoints (e.g., secure Mux uploads, management tasks)
│
├── auth/
│   ├── router.py              # Authentication routes (login, register, refresh tokens)
│   ├── deps.py                # Auth-related FastAPI dependencies (JWT validation, user extraction)
│
├── core/
│   ├── config.py              # Centralized environment configuration (loaded from .env via Pydantic)
│
├── courses/
│   ├── router.py              # REST endpoints for course creation, listing, and management
│
├── lessons/
│   ├── router.py              # Endpoints for lesson delivery, metadata, and Mux video references
│
├── models/
│   ├── sql/                   # Relational data models (PostgreSQL via SQLAlchemy)
│   │   ├── user.py            # User entity (credentials, roles, timestamps)
│   │   ├── enrollment.py      # User–Course enrollment model
│   │   ├── refresh_token.py   # Persistent refresh token storage (hashed)
│   │   ├── database.py        # Async SQLAlchemy engine, session factory, and Base metadata
│   │
│   ├── nosql/                 # NoSQL data schemas (MongoDB via Motor)
│       ├── course.py          # Course schema and structure for MongoDB
│       ├── lesson.py          # Lesson schema, including Mux asset references
│       ├── progress.py        # User progress tracking schema
│       ├── database.py        # MongoDB connection setup and database access layer
│
├── mux_webhooks/
│   ├── router.py              # Mux webhook routes (video.asset.created, video.asset.ready, etc.)
│
├── services/
│   ├── cache_service.py       # Redis caching layer for temporary data, tokens, and rate limiting
│   ├── mux_service.py         # Mux API client: asset creation, upload URL generation, event utilities
│   ├── refresh_token_ops.py   # Refresh token operations: rotation, revocation, persistence
│   ├── security.py            # Password hashing, JWT generation/verification, token utilities
│   ├── user_ops.py            # User-related business logic (registration, profile handling)
│
└── main.py                    # FastAPI entry point — creates the app, loads routers and settings

```
---

##  Author

**Adan Siqueira**  
🔗 [GitHub Profile](https://github.com/AdanSiqueira)

---

If you like this project, don’t forget to ⭐ **star the repository** to show your support!