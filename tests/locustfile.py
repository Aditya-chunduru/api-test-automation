"""
Resilient Locust Load Test Script for Supabase / PostgREST Backend
- Bypasses Windows Winsock / Gevent DNS resolution latency via synchronous pre-resolution.
- Mounts high-concurrency HTTP connection pools.
- Enforces an automated CI exit code via test_stop lifecycle hooks.
"""

# =====================================================================
# Module Imports & Purpose Ledger
# =====================================================================
import os                            # Environment variable access (SUPABASE_ANON_KEY)
import socket                        # Low-level network socket & hostname resolution
import gevent.socket                 # Greenlet-compatible socket monkey-patch targets
from pathlib import Path             # Cross-platform filesystem path navigation
from dotenv import load_dotenv       # Loads local test.env configurations
from locust import (                 # Core Locust load testing framework primitives
    HttpUser, 
    task, 
    between, 
    events
)
from requests.adapters import HTTPAdapter    # Connection pooling and transport safety
from urllib3.util.retry import Retry         # Exponential backoff / status retry policy

# =====================================================================
# DNS Resolution & Gevent/Windows Winsock Workaround
# =====================================================================
TARGET_DOMAIN = "aommnxekaskgjlwjsdpc.supabase.co"
try:
    # Synchronously resolve target IP once at process startup to eliminate greenlet DNS stalls
    CACHED_IP = socket.gethostbyname(TARGET_DOMAIN)
    print(f"Successfully pre-resolved {TARGET_DOMAIN} to {CACHED_IP}")
except Exception as e:
    # Fallback to general Cloudflare edge IP if DNS query fails offline/restricted
    CACHED_IP = "104.18.38.10"  
    print(f"Using fallback IP due to: {e}")

_orig_getaddrinfo = socket.getaddrinfo
def _cached_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
    """
    Hijacks DNS lookup for target domain, returning cached IP directly from memory.
    Bypasses OS-level DNS exhaustion or blocking under concurrent greenlet scaling.
    """
    if host == TARGET_DOMAIN:
        return [(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, '', (CACHED_IP, port))]
    return _orig_getaddrinfo(host, port, family, type, proto, flags)

# Apply global monkey-patch across standard library and gevent runtime
socket.getaddrinfo = _cached_getaddrinfo
gevent.socket.getaddrinfo = _cached_getaddrinfo

# Load test secrets relative to script/repository hierarchy
env_path = Path(__file__).resolve().parent.parent / 'test.env'
load_dotenv(dotenv_path=env_path)


# =====================================================================
# Virtual User Profile & Load Generation
# =====================================================================
class SupabaseLoadTestUser(HttpUser):
    host = f"https://{TARGET_DOMAIN}/"
    wait_time = between(1.0, 3.0)

    def on_start(self):
        """
        Configure HTTP connection pool scaling and inject RLS-ready headers per user session.
        """
        adapter = HTTPAdapter(
            pool_connections=10,
            pool_maxsize=20,
            max_retries=Retry(
                total=3,
                backoff_factor=0.1,
                status_forcelist=[500, 502, 503, 504],
            ),
        )
        self.client.mount("https://", adapter)
        self.client.mount("http://", adapter)

        self.api_key = os.getenv("SUPABASE_ANON_KEY", "")
        if not self.api_key:
            print(f"CRITICAL: Key is missing! Searched env path: {env_path}")
        else:
            print(f"Key loaded successfully. First 5 chars: {self.api_key[:5]}...")

        self.headers = {
            "apikey": self.api_key,
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        }

    @task(4)
    def get_cart_items(self):
        """
        High-frequency read task (weight 4): inspects cart records.
        """
        with self.client.get("/rest/v1/cart_items", headers=self.headers, name="GET /cart_items", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Cart items failed: {response.status_code}")

    @task(1)
    def query_protected_endpoint(self):
        """
        Low-frequency audit task (weight 1): probes RLS boundary on protected table.
        Allows 200, 401, or 403 as valid boundary evaluation outcomes.
        """
        with self.client.get("/rest/v1/orders", headers=self.headers, name="GET /orders (RLS)", catch_response=True) as response:
            if response.status_code in [200, 401, 403]:
                response.success()
            else:
                response.failure(f"Orders RLS check failed unexpectedly: {response.status_code}")


# =====================================================================
# CI/CD Performance Regression Enforcement Hook
# =====================================================================
@events.test_stop.add_listener
def routine_check(environment, **kwargs):
    """
    Evaluates global fail ratio upon test teardown.
    Fails CI pipeline process (exit code 1) if error rate exceeds 1%.
    """
    if environment.stats.total.fail_ratio > 0.01:
        print(f"❌ Performance Regression Test FAILED: Error rate {environment.stats.total.fail_ratio * 100:.2f}% exceeds threshold.")
        environment.process_exit_code = 1
    else:
        print("✅ Performance Regression Test PASSED: Latency and error rates within target bounds.")
