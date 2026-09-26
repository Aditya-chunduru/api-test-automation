"""
Slim/Optimized Locust Load Test User for Supabase / PostgREST Backend.
- Subclasses base SupabaseLoadTestUser for specialized slim projection and embedding validation.
- Mounts an aggressive high-concurrency HTTPAdapter per session.
- Guards against schema projection embedding rejections and structural contract drift.
"""

# =====================================================================
# Module Imports & Purpose Ledger
# =====================================================================
from locustfile import SupabaseLoadTestUser  # Base user class providing RLS auth header injection
from locust import task                      # Locust task weight decorator for runner scheduling
from requests.adapters import HTTPAdapter    # Low-level connection pool & transport configuration
from urllib3.util.retry import Retry         # Exponential backoff / status retry policy for transient edges


class SlimSupabaseLoadTestUser(SupabaseLoadTestUser):
    """
    Simulates high-frequency lean projection reads and PostgREST foreign-key joins.
    """

    def on_start(self):
        """
        Inherit base auth headers, then attach a tuned transport adapter 
        to prevent TCP socket queuing under concurrent virtual user ramps.
        """
        super().on_start()
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

    @task(4)
    def get_cart_items_slim(self):
        """
        Fetch partial-column projection (slim payload) to reduce wire serialization overhead.
        Validates HTTP 200 status and strict JSON array shape contract.
        """
        with self.client.get(
            "/rest/v1/cart_items?select=user_id,quantity,product_id",
            headers=self.headers,
            name="GET /cart_items (slim)",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if isinstance(data, list):
                        response.success()
                    else:
                        response.failure(f"Expected JSON array, got {type(data)}")
                except ValueError:
                    response.failure(f"Invalid JSON: {response.text[:60]}")
            else:
                self.assert_or_log(response, "GET /cart_items (slim)")

    @task(1)
    def get_orders_embedded_slim(self):
        """
        Test PostgREST relational embedding (orders -> profiles foreign-key projection) under RLS.
        Lower weight (1) mirrors heavier database compute cost from join resolution.
        """
        with self.client.get(
            "/rest/v1/orders?select=id,order_status,profiles(profiles_id,email)",
            headers=self.headers,
            name="GET /orders/profiles (embedded RLS, slim)",
            catch_response=True,
        ) as response:
            self.assert_or_log(response, "GET /orders/profiles (embedded RLS, slim)")

    def assert_or_log(self, response, name: str):
        """
        Standardized assertion/failure guard for catch_response blocks,
        truncating error text payloads to keep Locust stats legible.
        """
        if response.status_code == 200:
            response.success()
        else:
            response.failure(f"[{name}] {response.status_code}: {response.text[:120]}")
