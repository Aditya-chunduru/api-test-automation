import os
import socket
import gevent.socket
from pathlib import Path
from dotenv import load_dotenv
from locust import HttpUser, task, between
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
    wait_time = between(0.5, 2.0)

    def on_start(self):
        adapter = HTTPAdapter(
            pool_connections=50,
            pool_maxsize=50,
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
        print(f"Sending Headers: {self.headers}")
    @task(4)
    def get_cart_items(self):
        self.client.get("/rest/v1/cart_items", headers=self.headers, name="GET /cart_items")

    @task(1)
    def query_protected_endpoint(self):
        self.client.get("/rest/v1/orders", headers=self.headers, name="GET /orders (RLS)")