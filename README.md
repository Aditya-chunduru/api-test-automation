# Supabase API Test Automation & Performance Framework

A production-grade, automated API testing and concurrency regression framework built for PostgreSQL and Supabase backend environments. Features multi-tier Row-Level Security (RLS) enforcement, schema/contract validation via `pytest`, and connection-pooled load verification via `locust`.

## 🛠️ Tech Stack
* **Language**: Python 3.11
* **Database / Backend**: PostgreSQL, Supabase (REST API / Auth / RLS)
* **Testing Framework**: pytest (Requests, Python-Dotenv, Urllib3 Retry Adapters)
* **Load Testing**: Locust (Custom connection pooling & telemetry CSV archiving)
* **CI/CD**: GitHub Actions (Dual-pipeline regression gates)

## 📂 Project Architecture
```text
├── .github/workflows/
│   ├── load_test.yml       # Ad-hoc / manual load execution
│   ├── locust-gate.yml     # Automated Locust concurrency & 1% error-rate gate
│   ├── pytest.yml          # Functional & multi-tier RLS regression suite
│   └── test.yml            # Core pipeline validation / smoke test
├── tests/
│   ├── conftest.py         # Dynamic JWT auth, role fixtures, HTTP session factories
│   ├── test_api.py         # Contract, schema projection, and 404 handling
│   ├── test_rls_security.py # Multi-tier RLS isolation & privilege escalation blocks
│   ├── test_supabase.py    # Direct table query/pagination health checks
│   ├── locustfile.py       # High-concurrency RPS stress scenarios
│   └── locust_wrapper.py   # Telemetry and runner wrapper
└── test.env                # Local environment configuration parity
```

## 🚀 Key Technical Highlights
 * **Dynamic JWT Lifecycle Management & Role Isolation (conftest.py)**
 * Programmatically fetches fresh user tokens via Supabase Auth POST endpoints, segregating test execution across anonymous, authenticated, and restricted role contexts.


* **Multi-Tier RLS Security Matrix (test_rls_security.py)**
* Verifies data isolation boundaries, ensuring unauthenticated requests are dropped and cross-owner mutations trigger proper PostgREST authorization blocks.


* **Resilient Connection Pooling:**
* Utilizes custom HTTPAdapter configurations (pool_maxsize=20) paired with exponential backoff retry strategies (urllib3.Retry) to eliminate TCP socket exhaustion under load.

* **Headless Telemetry Gates:**
* Enforces strict error-rate ceilings (<1%) via automated Locust CLI flags (--headless, --csv) with artifact archiving for audit trails.

## 🔄 CI/CD Automation

* **Integrated via GitHub Actions (.github/workflows/), automating secret provisioning, dependency caching, and dual-gate validation across pull requests and pushes:**

* Functional / Smoke Gates (pytest.yml, test.yml): Validates API contracts, schema integrity, and RLS security boundaries.
* Performance / Concurrency Gates (locust-gate.yml, load_test.yml): Executes headless load testing and archives CSV telemetry reports.
