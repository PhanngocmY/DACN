import os
import time
import httpx
from typing import Tuple, Optional, Dict
from api.models import DecisionRequest

class EngineKeycloak:
    def __init__(self, keycloak_url: str = None, realm: str = "k6-lab", client_id: str = "k6-decision-api", client_secret: str = "doi-bi-mat-lab", password: str = "Lab@2026!"):
        self.keycloak_url = (keycloak_url or os.getenv("KEYCLOAK_URL", "http://keycloak:8080")).rstrip("/")
        self.realm = realm
        self.client_id = client_id
        self.client_secret = client_secret
        self.password = password
        self.token_url = f"{self.keycloak_url}/realms/{self.realm}/protocol/openid-connect/token"
        self.client = httpx.Client(timeout=10.0)
        self.token_cache: Dict[str, Optional[str]] = {}

    def get_user_token(self, username: str) -> Optional[str]:
        """
        Lấy Access Token cho user bằng Password Grant và cache lại để không làm chậm lúc benchmark.
        """
        if username == "khach_la":
            return None

        if username in self.token_cache:
            return self.token_cache[username]

        payload = {
            "grant_type": "password",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "username": username,
            "password": self.password
        }

        try:
            resp = self.client.post(self.token_url, data=payload)
            if resp.status_code == 200:
                token = resp.json().get("access_token")
                self.token_cache[username] = token
                return token
            else:
                self.token_cache[username] = None
                return None
        except Exception as e:
            print(f"[EngineKeycloak] Warning: Failed to obtain token for {username}: {e}")
            return None

    def authorize(self, req: DecisionRequest) -> Tuple[str, float]:
        """
        Thực thi phân quyền bằng UMA Ticket Grant (response_mode=decision).
        Chỉ đo độ trễ của bước thẩm định quyền (không tính bước cấp token).
        """
        token = self.get_user_token(req.subject)
        if not token:
            return "deny", 0.0

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/x-www-form-urlencoded"
        }

        # Định dạng permission: <resource_id>#<action> (ví dụ: DC-CNTT-001#edit)
        permission_str = f"{req.resource.id}#{req.action}"

        payload = {
            "grant_type": "urn:ietf:params:oauth:grant-type:uma-ticket",
            "audience": self.client_id,
            "permission": permission_str,
            "response_mode": "decision"
        }

        start_time = time.perf_counter()
        try:
            resp = self.client.post(self.token_url, headers=headers, data=payload)
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0

            if resp.status_code == 200:
                data = resp.json()
                if data.get("result") is True:
                    return "allow", elapsed_ms
            return "deny", elapsed_ms
        except Exception as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            print(f"[EngineKeycloak] Error: {e}")
            return "deny", elapsed_ms
