# Personalized Learning Path Optimizer (PLPO)

> **Theme:** Generative AI and LLM Applications  
> **Phase:** Phase 4 — Scalability, Reliability, and Production Readiness  
> **Technology Stack:** Pure Python & Streamlit Native, SQLAlchemy 2.0, PostgreSQL 16 + pgvector, Redis, Prometheus

---

## 📌 Project Overview

The **Personalized Learning Path Optimizer (PLPO)** is an enterprise-grade adaptive educational AI platform engineered to dynamically model a student's evolving knowledge state, confidence calibration, cognitive misconceptions, and prerequisite dependencies.

Unlike static courseware or generic conversational chatbots, PLPO implements a closed-loop adaptive cycle backed by relational persistence, semantic vector retrieval via **pgvector**, multi-level caching, structured JSON logging, and Prometheus metrics observability.

### Core Adaptive Loop
```
ASSESS (Diagnostic Question with 1-5 Metacognitive Confidence)
  ↓
ANALYZE (Calibrate Confidence vs Correctness into 4 Quadrants)
  ↓
IDENTIFY KNOWLEDGE GAP (Multi-signal Mastery & Performance Buffer)
  ↓
CHECK PREREQUISITES (Hierarchical DAG Dependency Verification)
  ↓
DETECT POSSIBLE MISCONCEPTION (Diagnose Entrenched Mental Model Bugs)
  ↓
GENERATE INTERVENTION (Explanation → Analogy → Side-by-Side Code Contrast → Follow-Up)
  ↓
PRACTICE (Dynamically Synthesized Deliberate Practice Micro-Drills)
  ↓
REASSESS (Targeted Verification of Conceptual Stability)
  ↓
UPDATE KNOWLEDGE STATE (Bayesian Evidence Integration & Relational Persistence)
  ↓
RECALCULATE LEARNING PATH (Dynamic Path Reordering & Prerequisite Unlock)
```

The learning path is **not static or hardcoded**. Every interaction recalculates the student's curricular trajectory in real time and persists state changes directly to the database.

---

## 🏗️ Project Architecture (Phase 4 — Enterprise Production)

```
d:/PLPO/
│
├── app.py                          # Streamlit entrypoint, session coordinator, RBAC & service wiring
├── requirements.txt                # Production dependencies (SQLAlchemy, psycopg2, pgvector, prometheus)
├── Dockerfile                      # Multi-stage production container build (non-root user, healthcheck)
├── docker-compose.yml              # Full-stack composition (App, PostgreSQL+pgvector, Redis, Prometheus)
├── README.md                       # Comprehensive system guide
├── .env.example                    # Production environment configuration template
├── .gitignore                      # Git exclusions for credentials, secrets, cache, and db files
│
├── core/                           # System Intelligence, Security & Infrastructure Backend
│   ├── db/                         # PostgreSQL + pgvector & SQLite Dual-Mode Persistence
│   │   ├── session.py              # Engine management, connection pooling, scoped sessions
│   │   ├── models.py               # SQLAlchemy ORM models (Student, Mastery, Attempts, Embeddings)
│   │   ├── repository.py           # Repository layer (Student, KnowledgeState, Assessment, Audit, Vector)
│   │   ├── init_db.py              # Schema bootstrap & demo data seeding module
│   │   └── migrations/             # SQL DDL migrations with HNSW pgvector index
│   │
│   ├── cache/                      # Multi-Level Caching System
│   │   └── cache_manager.py        # Thread-safe LRU cache with TTL & Redis cluster client
│   │
│   ├── background/                 # Asynchronous Task Execution
│   │   └── task_queue.py           # ThreadPool background worker for non-blocking operations
│   │
│   ├── telemetry/                  # Observability, Metrics & Diagnostics
│   │   ├── logger.py               # Structured JSON logger (Datadog/CloudWatch ready)
│   │   ├── metrics.py              # Prometheus metric counters, histograms, and gauges
│   │   ├── health.py               # End-to-end system health check (/healthz)
│   │   └── error_tracker.py        # Sentry SDK integration with in-memory ring-buffer
│   │
│   ├── services/                   # Clean Decoupled API Service Boundaries
│   │   ├── adaptive_service.py     # Orchestrator for the 10-step adaptive learning loop
│   │   └── student_service.py      # Profile management & baseline resets
│   │
│   ├── security.py                 # Adversarial resilience, prompt injection firewall, rate limiter
│   ├── auth.py                     # Role-Based Access Control (Student, Instructor, Admin) & sessions
│   ├── student_profile.py          # Student profile domain entity
│   ├── assessment.py               # Diagnostic assessment engine & attempt telemetry
│   ├── knowledge_state.py          # Bayesian multi-signal knowledge engine & audit records
│   ├── confidence.py               # Metacognitive confidence calibration analyzer (4 quadrants)
│   ├── misconception.py            # Cognitive misconception catalog & 4-part remediation model
│   ├── prerequisites.py            # Curricular Directed Acyclic Graph (DAG)
│   ├── optimizer.py                # Dynamic learning path optimizer & adaptation changelog
│   ├── practice_generator.py       # Deliberate micro-practice generator
│   │
│   └── ai/                         # Server-Side Modular AI Provider Architecture
│       ├── base.py                 # BaseAIProvider abstract interface
│       ├── schema.py               # Pydantic schemas (StudentDiagnosticAnalysis, SocraticTutorResponse)
│       ├── gemini_provider.py      # Google Gemini 1.5 Flash provider + deterministic offline fallback
│       └── tutor_service.py        # Context-aware Socratic AI Tutor & injection guard
│
├── pages/                          # Streamlit View Controllers (100% Native Components)
│   ├── dashboard.py                # Student cognitive profile, live state diffs, charts & path preview
│   ├── assessment.py               # Diagnostic assessment with 1-5 confidence, timing, 4-part intervention
│   ├── learning_path.py            # Dynamic curricular pathway, adaptation log & before/after diffs
│   ├── practice.py                 # Targeted micro-drills generated from weak topics & misconceptions
│   ├── tutor.py                    # Socratic AI Tutor, Pydantic JSON inspector & Adversarial playground
│   └── analytics.py                # Stored-data analytics & Production Health / Prometheus tab
│
├── components/                     # Reusable UI & Visualization Components
│   ├── sidebar.py                  # RBAC persona switcher, 1-Click Judge Demo Walkthrough, AI status
│   ├── cards.py                    # Native metric cards, progress bars, and alerts (Zero raw HTML)
│   ├── charts.py                   # Plotly visualizations (mastery radar, calibration quadrant, timelines)
│   └── learning_path_view.py       # Connected curricular node flow visualizer (KaTeX-safe)
│
├── deploy/                         # Production Deployment Configurations
│   ├── k8s/                        # Kubernetes Deployment, Service, Ingress, HPA, ConfigMap, Secrets
│   ├── nginx/                      # Nginx reverse proxy with WebSocket upgrade & rate limiting
│   └── prometheus/                 # Prometheus scraper configuration
│
├── tests/                          # Automated Pytest Suite (20 Tests, 100% Pass Rate)
│   ├── test_adaptive_loop.py       # Full adaptive cycle verification
│   ├── test_persistence_db.py     # Relational & vector database repository tests
│   ├── test_security_resilience.py # Adversarial injection, bounds check, and RBAC tests
│   ├── test_caching.py             # LRU, TTL, and memoization decorator tests
│   └── test_telemetry.py           # Prometheus metrics and health check tests
│
├── docs/
│   └── ARCHITECTURE.md             # Comprehensive production architecture & scaling documentation
│
└── data/
    └── demo_data.py                # Verified baseline student records & curricular fixtures
```

---

## 🌟 Phase 4 Implemented Capabilities

### 1. PostgreSQL & pgvector Relational Persistence
- **Dual-Mode Engine**: Operates with SQLite (`sqlite:///data/plpo.db`) out-of-the-box for instant local prototyping with zero setup, and switches automatically to production PostgreSQL when `DATABASE_URL` is set.
- **Relational Integrity**: Foreign keys with `ON DELETE CASCADE`, composite indexes on `(student_id, topic_name)` and `(student_id, created_at DESC)`.
- **pgvector Integration**: Stores 768-dimensional embeddings of curriculum chunks with an **HNSW vector index** (`hnsw (embedding vector_cosine_ops)`) for sub-millisecond semantic retrieval.

### 2. Multi-Level Caching (`core/cache/`)
- Thread-safe in-memory LRU cache with TTL expiration and declarative memoization decorator `@cached`.
- Ready for distributed **Redis** clustering via `REDIS_URL` for multi-pod Kubernetes deployments.

### 3. Background Task Runner (`core/background/`)
- Asynchronous `ThreadPoolExecutor` worker queue (`GLOBAL_TASK_QUEUE`) preventing UI freezes during heavy curricular DAG evaluations, batch drill generation, and embedding indexing.

### 4. Full Observability & Prometheus Metrics (`core/telemetry/`)
- **Prometheus Metrics**: Counters, histograms, and gauges exposed for scraping:
  - `plpo_assessments_total`
  - `plpo_path_reoptimizations_total`
  - `plpo_misconceptions_detected_total` & `plpo_misconceptions_remediated_total`
  - `plpo_ai_requests_total`
  - `plpo_adversarial_violations_total`
  - `plpo_db_query_duration_seconds`
- **Structured JSON Logging**: Single-line JSON log objects with ISO timestamps, trace IDs, and event metadata for ingestion into ELK/Datadog/CloudWatch.
- **Health Check Endpoint**: `/healthz` verifying database latency, cache status, and host system CPU/memory.
- **Error Tracking**: Captures exceptions with stack traces (`ErrorTracker`), integrated with Sentry SDK.

### 5. Automated Pytest Test Suite
- Comprehensive suite of 20 unit and integration tests covering the adaptive loop, database persistence, adversarial resilience, caching, and telemetry:
```
======================= 20 passed, 14 warnings in 2.32s =======================
```

### 6. Cloud Deployment & CI/CD Pipeline
- **Docker**: Multi-stage lightweight Dockerfile running as non-root user `plpo_user`.
- **Docker Compose**: One-command stack running PLPO, PostgreSQL 16 + pgvector, Redis 7, and Prometheus.
- **Kubernetes**: Production manifests with Horizontal Pod Autoscaler (2-10 pods), Ingress with WebSocket upgrade annotations, ClusterIP services, and Secrets.
- **GitHub Actions**: Automated CI/CD pipeline (`.github/workflows/ci.yml`) running linting, compilation checks, pytest suite, and container image builds.

---

## 🎯 Verification & Running Instructions

### Run Automated Tests
```bash
pytest tests/ -v
```

### Run Locally with Python / Streamlit
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Initialize database and seed baseline data
python -m core.db.init_db

# 3. Launch application
streamlit run app.py
```
App will be accessible at `http://localhost:8501`.

### Run Full Production Stack with Docker Compose
```bash
docker compose up -d --build
```
- App UI: `http://localhost:8501`
- Prometheus: `http://localhost:9090`
- PostgreSQL: `localhost:5432`

---

## 📖 In-Depth Documentation
For detailed architectural diagrams, database schemas, scaling strategies, and security documentation, please consult **[ARCHITECTURE.md](docs/ARCHITECTURE.md)**.
