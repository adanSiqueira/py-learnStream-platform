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


### Database Architecture 

The app applies a **hybrid database strategy**, designed according to the **PACELC theorem**. 

<div align="center">
    <img src="./src/pacelc.jpg" alt="pacelc" width="1000" height = "550" style="margin-bottom: 1.0em;"/>
</div>

#### Design Rationale
- **Availability (A)** and **Low Latency (L)** are prioritized for course consumption and progress tracking, ensuring users always have access to their learning content. In an online learning platform, availability and responsiveness directly impact user experience — learners must always be able to access courses, watch lessons, and have their progress updated, even during network partitions or node failures. For this reason, AP/EL (Available–Partition tolerant / Else–Low latency) systems like MongoDB are ideal for progress tracking, analytics, and content delivery, where minor delays in synchronization are acceptable. 
- **Consistency (C)** is enforced on authentication, user management, and core course data to preserve data integrity. Components that require transactional integrity — such as authentication, roles, payments, and course metadata — demand CP/EC (Consistent–Partition tolerant / Else–Consistent) systems like PostgreSQL to prevent conflicts and maintain data reliability.
- The result is an **AP/EL + CP/EC hybrid system**, combining the strengths of relational and non-relational storage.

### Stack
| Layer | Purpose | Technology |
|-------|----------|-------------|
| **Relational (CP/EC)** | Users, authentication, roles, course metadata | PostgreSQL + SQLAlchemy |
| **NoSQL (AP/EL)** | Lesson progress, analytics, watch history | MongoDB + Motor |
| **Cache Layer** | Caching, sessions, rate limiting | Redis + aioredis |
| **Async API Layer** | High-performance backend | FastAPI |
| **Streaming API** | Secure video hosting and delivery | Mux API |






