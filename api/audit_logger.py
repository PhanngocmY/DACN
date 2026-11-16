import os
import json
from datetime import datetime, timezone

class AuditLogger:
    def __init__(self, log_path: str = "/app/evidence/audit.jsonl"):
        self.log_path = log_path
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)

    def log(self, subject: str, action: str, resource: str, decision: str, reason: str, engine: str, latency_ms: float, end_to_end_ms: float):
        entry = {
            "subject": subject,
            "action": action,
            "resource": resource,
            "decision": decision,
            "reason": reason,
            "engine": engine,
            "ts": datetime.now(timezone.utc).isoformat(),
            "latency_ms": round(latency_ms, 3),
            "end_to_end_ms": round(end_to_end_ms, 3)
        }
        try:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"[AuditLogger] Warning: Could not write log to {self.log_path}: {e}")
