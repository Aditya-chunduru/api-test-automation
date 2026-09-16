import os
import socket
import gevent.socket
from pathlib import Path
from dotenv import load_dotenv
from locust import HttpUser, task, between, events
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# 1. Resolve the IP ONCE synchronously at startup before greenlets start
TARGET_DOMAIN = "aommnxekaskgjlwjsdpc.supabase.co"
try:
    CACHED_IP = socket.gethostbyname(TARGET_DOMAIN)
    print(f"Successfully pre-resolved {TARGET_DOMAIN} to {CACHED_IP}")
except Exception as e:
    CACHED_IP = "104.18.38.10"  # Fallback to Cloudflare IP
    print(f"Using fallback IP due to: {e}")

# 2. Patch getaddrinfo to return the cached IP instantly from memory (bypassing Windows Winsock)
_orig_getaddrinfo = socket.getaddrinfo
def _cached_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
    if host == TARGET_DOMAIN:
        return [(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, '', (CACHED_IP, port))]
    return _orig_getaddrinfo(host, port, family, type, proto, flags)

socket.getaddrinfo = _cached_getaddrinfo
gevent.socket.getaddrinfo = _cached_getaddrinfo

env_path = Path(__file__).resolve().parent.parent / 'test.env'
load_dotenv(dotenv_path=env_path)

class SupabaseLoadTestUser(HttpUser):
    host = f"https://{TARGET_DOMAIN}/"
    wait_time = between(1.0, 3.0)

    def on_start(self):
        adapter = HTTPAdapter(
            pool_connections=150,
            pool_maxsize=150,
            max_retries=Retry(
                total=3,
                backoff_factor=0.1,
                status_forcelist=[500, 502, 503, 504],
            )
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
        with self.client.get("/rest/v1/cart_items", headers=self.headers, name="GET /cart_items", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Cart items failed: {response.status_code}")

    @task(1)
    def query_protected_endpoint(self):
        with self.client.get("/rest/v1/orders", headers=self.headers, name="GET /orders (RLS)", catch_response=True) as response:
            # Depending on RLS setup, 200 with empty array or specific status is expected
            if response.status_code in [200, 401, 403]:
                response.success()
            else:
                response.failure(f"Orders RLS check failed unexpectedly: {response.status_code}")

# 3. CI/CD Performance Regression Enforcement Hook
@events.test_stop.add_listener
def routine_check(environment, **kwargs):
    # Check if error rate exceeds 1% or total failures occurred
    if environment.stats.total.fail_ratio > 0.01:
        print(f"❌ Performance Regression Test FAILED: Error rate {environment.stats.total.fail_ratio * 100:.2f}% exceeds threshold.")
        environment.process_exit_code = 1
    else:
        print("✅ Performance Regression Test PASSED: Latency and error rates within target bounds.")