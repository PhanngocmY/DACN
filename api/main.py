import time
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from api.models import DecisionRequest, DecisionResponse
from api.reason_helper import ReasonHelper
from api.audit_logger import AuditLogger
from api.engine_opa import EngineOPA
from api.engine_cedar import EngineCedar
from api.engine_keycloak import EngineKeycloak

app = FastAPI(
    title="Unified Authorization Decision API",
    description="API gateway chuẩn hóa phục vụ so sánh 3 engine: OPA, Cedar và Keycloak",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Khởi tạo các helper và engine adapters
reason_helper = ReasonHelper()
audit_logger = AuditLogger()
engine_opa = EngineOPA()
engine_cedar = EngineCedar()
engine_keycloak = EngineKeycloak()

@app.get("/health")
def health_check():
    return {"status": "ok", "engines": ["opa", "cedar", "keycloak"]}

@app.post("/authorize", response_model=DecisionResponse)
def authorize(req: DecisionRequest):
    e2e_start = time.perf_counter()

    # 1. Điều hướng thực thi theo engine
    if req.engine == "opa":
        decision, latency_ms = engine_opa.authorize(req)
    elif req.engine == "cedar":
        decision, latency_ms = engine_cedar.authorize(req)
    elif req.engine == "keycloak":
        decision, latency_ms = engine_keycloak.authorize(req)
    else:
        raise HTTPException(status_code=400, detail=f"Engine '{req.engine}' không được hỗ trợ.")

    e2e_ms = (time.perf_counter() - e2e_start) * 1000.0

    # 2. Sinh lý do khách quan (không lộ PII per NFR-04)
    reason = reason_helper.evaluate_reason(
        subject=req.subject,
        action=req.action,
        resource_type=req.resource.type,
        resource_id=req.resource.id,
        decision=decision
    )

    # 3. Ghi audit log (DR-04 và FR-07)
    audit_logger.log(
        subject=req.subject,
        action=req.action,
        resource=req.resource.id,
        decision=decision,
        reason=reason,
        engine=req.engine,
        latency_ms=latency_ms,
        end_to_end_ms=e2e_ms
    )

    return DecisionResponse(
        decision=decision,
        reason=reason,
        engine=req.engine,
        latency_ms=round(latency_ms, 3),
        end_to_end_ms=round(e2e_ms, 3)
    )
