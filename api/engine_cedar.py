import os
import time
import json
from typing import Tuple
from api.models import DecisionRequest

try:
    import cedarpy
    from cedarpy import Decision
except ImportError:
    cedarpy = None
    Decision = None

class EngineCedar:
    def __init__(self, policies_path: str = None, entities_path: str = None):
        self.policies_path = policies_path or os.getenv("CEDAR_POLICIES_PATH", "/app/policies/cedar/policies.cedar")
        self.entities_path = entities_path or os.getenv("CEDAR_ENTITIES_PATH", "/app/data/cedar_entities.json")
        self.policies_str = ""
        self.entities_str = "[]"
        self._load_files()

    def _load_files(self):
        if os.path.exists(self.policies_path):
            with open(self.policies_path, "r", encoding="utf-8") as f:
                self.policies_str = f.read()
        if os.path.exists(self.entities_path):
            with open(self.entities_path, "r", encoding="utf-8") as f:
                self.entities_str = f.read()

    def authorize(self, req: DecisionRequest) -> Tuple[str, float]:
        """
        Thực thi phân quyền bằng Cedar engine nhúng (cedarpy).
        Trả về: (decision ["allow"|"deny"], latency_ms)
        """
        if not cedarpy:
            return "deny", 0.0

        # Ánh xạ resource type sang PascalCase: Syllabus hoặc Course
        res_type = "Syllabus" if req.resource.type.lower() == "syllabus" else "Course"

        request = {
            "principal": f'User::"{req.subject}"',
            "action": f'Action::"{req.action}"',
            "resource": f'{res_type}::"{req.resource.id}"',
            "context": {}
        }

        start_time = time.perf_counter()
        try:
            result = cedarpy.is_authorized(
                request=request,
                policies=self.policies_str,
                entities=self.entities_str
            )
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0

            if result.decision == Decision.Allow:
                return "allow", elapsed_ms
            return "deny", elapsed_ms
        except Exception as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            # Với ca chủ thể không tồn tại (LM09 khach_la), lỗi thuộc tính dẫn tới mặc định deny
            return "deny", elapsed_ms
