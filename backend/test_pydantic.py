from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Any

class KnowledgeRelationshipResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    project_id: str
    source: str
    relation: str
    target: str
    confidence: float
    metadata: dict[str, Any] = Field(validation_alias="meta")
    created_at: datetime
    updated_at: datetime

class ORMModel:
    def __init__(self):
        self.id = 1
        self.project_id = "test"
        self.source = "A"
        self.relation = "B"
        self.target = "C"
        self.confidence = 0.9
        self.meta = {"key": "value"}
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

try:
    obj = ORMModel()
    response = KnowledgeRelationshipResponse.model_validate(obj)
    print(response.model_dump())
    print("SUCCESS")
except Exception as e:
    print(f"FAILED: {e}")
