# Supabase API Test Automation & Performance Framework

A robust, automated API testing and concurrency framework built for PostgreSQL and Supabase backend environments. This repository features comprehensive functional validation, Row-Level Security (RLS) checks using `pytest`, and high-concurrency performance load-testing using `Locust`.

---

## 🛠️ Tech Stack
* **Language:** Python 3.11
* **Database / Backend:** PostgreSQL, Supabase (REST API / Auth)
* **Testing Framework:** `pytest` (Requests, Python-Dotenv)
* **Load Testing:** Locust (Custom socket patching & connection pooling)
* **CI/CD:** GitHub Actions

---

## 📂 Project Architecture

```text
├── conftest.py          # Centralized pytest fixtures for dynamic JWT auth, sessions, and roles
├── test_api.py          # Functional tests for API endpoints and schema validation
├── test_rls_security.py # Security validation tests for Row-Level Security and auth blocks
├── locustfile.py        # High-concurrency load testing with custom Winsock/DNS patching
└── test.env             # Environment configuration
```

# 🚀 Key Technical Highlights
 * **Dynamic JWT Lifecycle Management & Role Isolation (conftest.py)**
 * Automated Authentication: Automatically executes a programmatic POST request to Supabase's auth endpoint to fetch a fresh JWT user token before test execution.
 * Session Scope & Fixtures: Manages session-scoped and function-scoped fixtures to cleanly segregate testing across authenticated_api_session, anonymous_api_session, and restricted_api_session to validate authorization constraints.


* **Rigorous Security & RLS Verification (test_rls_security.py)**
* Programmatically verifies that unauthenticated and unauthorized roles are properly blocked by database Row-Level Security (RLS) policies.
* Tests data mutation permissions to prevent privilege escalation and unauthorized record modifications.


* **Low-Level Network Optimization & Load Testing (locustfile.py)**
* **DNS & Socket Patching:** Engineered a custom low-level gevent socket patch to pre-resolve target domain IP addresses synchronously at startup, completely bypassing Winsock resolution latency during virtual-user spawning.

* **Connection Pooling:** Utilizes a custom HTTPAdapter configured with high connection limits and exponential backoff retry strategies to benchmark backend stability under heavy load.

# 🔄 CI/CD Automation

* Integrated into GitHub Actions workflows (.github/workflows/), ensuring that every pull request and push automatically provisions environment secrets, installs dependencies, and executes the complete test suite headlessly.
