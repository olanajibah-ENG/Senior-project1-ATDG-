from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field
from bson import ObjectId
from core_ai.models.codefile import PyObjectId


class ProjectAnalysisResult(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    project_id:        str      = ""
    dependency_order:  list     = []
    dependency_graph:  dict     = {}
    contexts:          dict     = {}
    analysis_ids:      list     = []
    project_summary:   str      = ""
    status:            str      = "PENDING"
    created_at:        datetime = Field(default_factory=datetime.utcnow)

    class Config:
        validate_by_name        = True
        arbitrary_types_allowed = True
        json_encoders           = {ObjectId: str}
