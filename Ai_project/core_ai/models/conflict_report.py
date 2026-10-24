from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime


class ConflictReport(BaseModel):
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
    }

    id: Optional[str] = Field(None, alias="_id")

    project_id:     str
    file_id:        str
    version_a_id:   Optional[str] = None
    version_b_id:   Optional[str] = None
    doc_version_id: Optional[str] = None

    analysis_type: str

    analysis_a_id:  Optional[str] = None
    analysis_b_id:  Optional[str] = None
    explanation_id: Optional[str] = None

    structural_conflicts: List[Dict[str, Any]] = Field(default_factory=list)
    semantic_conflicts:   List[Dict[str, Any]] = Field(default_factory=list)
    doc_conflicts:        List[Dict[str, Any]] = Field(default_factory=list)

    summary:                str   = ""
    breaking_changes_count: int   = 0
    compatibility_score:    Optional[float] = None
    total_conflicts:        int   = 0
    grade:                  str   = "B"

    suggestions: List[Dict[str, Any]] = Field(default_factory=list)

    status:  str           = "pending"
    task_id: Optional[str] = None
    error:   Optional[str] = None

    created_at:             datetime       = Field(default_factory=datetime.utcnow)
    updated_at:             datetime       = Field(default_factory=datetime.utcnow)
    completed_at:           Optional[datetime] = None
    execution_time_seconds: Optional[float]    = None
