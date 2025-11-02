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

LearnStream Platform is a FastAPI-based backend for managing online courses and secure video lessons.


### Features
- User login and JWT authentication
- Role-based access control
- Track course progress
- Stream video lessons using Mux API
- SQL or NoSQL database support

### Tech Stack
- Python 3.11
- FastAPI
- SQLAlchemy/PostgreSQL or Motor/MongoDB
- PyJWT, Passlib
- Mux API

---
### Database Architecture 

The app applies a **hybrid database strategy**, designed according to the **PACELC theorem**. 

<div align="center">
    <img src="./src/pacelc.jpg" alt="pacelc" width="1000" height = "550" style="margin-bottom: 1.0em;"/>
</div>

#### Design Rationale

* **Availability (A)** and **Low Latency (L)** are prioritized for course and lesson delivery, ensuring learners can always access educational content, even in case of network partitions or replication delays. In an online learning platform, uninterrupted access to lessons and progress updates outweighs immediate synchronization — users expect to study anytime, anywhere. For that reason, **AP/EL systems** like **MongoDB** are chosen for **courses, lessons, progress tracking, analytics, and watch history**, where temporary inconsistencies are acceptable in favor of responsiveness and uptime.
* **Consistency (C)** is strictly enforced for **authentication, user management, enrollments, and payments**, since these components require transactional integrity and conflict prevention. **CP/EC systems** like **PostgreSQL** ensure strong consistency, guaranteeing reliable access control and accurate financial operations.
* The result is a **hybrid AP/EL + CP/EC architecture**, leveraging the high availability of NoSQL for content and progress data, while maintaining strong consistency and integrity in user and transactional layers.

### Stack

| Layer                  | Purpose                                                       | Technology              |
| ---------------------- | ------------------------------------------------------------- | ----------------------- |
| **Relational (CP/EC)** | Users, authentication, roles, enrollments, payments           | PostgreSQL + SQLAlchemy |
| **NoSQL (AP/EL)**      | Courses, lessons, progress tracking, analytics, watch history | MongoDB + Motor         |
| **Cache Layer**        | Caching, sessions, rate limiting                              | Redis + aioredis        |
| **Async API Layer**    | High-performance backend                                      | FastAPI                 |
| **Streaming API**      | Secure video hosting and delivery                             | Mux API                 |

---
##  Security and Authentication Design

The authentication system follows **JWT-based stateless security**, designed for distributed and asynchronous environments, with the following premises stablished:

1. **Access Tokens are not stored in the database**: Access tokens are **short-lived and stateless**, carrying all user claims internally. This enables horizontal scalability and reduces latency, since the server can verify tokens without querying the database. Once expired, access tokens are simply discarded instead of invalidated manually.

2. **Refresh Tokens are hased stored, to allow revocation**: Refresh tokens are **long-lived** and can generate new access tokens without requiring a full login. Storing them allows the server to revoke compromised sessions or implement logout mechanisms securely. By storing only a **one-way hash**, even if the DB is leaked, tokens cannot be used. Hashing acts as a **second layer of defense**, just as password hashing does.


---







