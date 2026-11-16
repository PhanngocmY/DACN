from pydantic import BaseModel, Field
from typing import Literal, Optional

class ResourceModel(BaseModel):
    type: str = Field(..., description="Loại resource: 'syllabus' hoặc 'course'")
    id: str = Field(..., description="ID resource: ví dụ 'DC-CNTT-001', 'LMS-ATTT01'")

class DecisionRequest(BaseModel):
    subject: str = Field(..., description="Username chủ thể: ví dụ 'gv_cntt_01', 'sv_01'")
    action: str = Field(..., description="Hành động: 'view' hoặc 'edit'")
    resource: ResourceModel
    engine: Literal["opa", "cedar", "keycloak"] = Field(..., description="Engine xử lý phân quyền")

class DecisionResponse(BaseModel):
    decision: Literal["allow", "deny"]
    reason: str
    engine: str
    latency_ms: float
    end_to_end_ms: Optional[float] = None
