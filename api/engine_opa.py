import os
import time
import httpx
from typing import Tuple
from api.models import DecisionRequest

class EngineOPA:
    def __init__(self, opa_url: str = None):
        self.opa_url = opa_url or os.getenv("OPA_URL", "http://opa:8181/v1/data/authz/allow")
        self.client = httpx.Client(timeout=5.0)

    def authorize(self, req: DecisionRequest) -> Tuple[str, float]:
        """
        Gửi yêu cầu phân quyền tới OPA server.
        Trả về: (decision ["allow"|"deny"], latency_ms)
        """
        payload = {
            "input": {
                "subject": req.subject,
                "action": req.action,
                "resource": {
                    "type": req.resource.type.lower(),
                    "id": req.resource.id
                }
            }
        }

        start_time = time.perf_counter()
        try:
            resp = self.client.post(self.opa_url, json=payload)
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0

            if resp.status_code == 200:
                data = resp.json()
                # OPA trả về {"result": true} hoặc {"result": false}
                if data.get("result") is True:
                    return "allow", elapsed_ms
            return "deny", elapsed_ms
        except Exception as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            print(f"[EngineOPA] Error: {e}")
            return "deny", elapsed_ms
