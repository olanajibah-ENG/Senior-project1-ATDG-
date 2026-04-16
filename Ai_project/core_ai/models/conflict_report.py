from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
from core_ai.services.conflict_detection.schemas import ConflictItem

class ConflictReport(BaseModel):
    """هيكل تقرير التناقضات لـ MongoDB"""
    id: Optional[str] = Field(None, alias="_id")
    project_id: str
    version_a: str
    version_b: Optional[str] = None
    
    analysis_type: str  # code_vs_code, code_vs_doc, full_analysis
    
    # تخزين النتائج (قوائم التناقضات)
    structural_conflicts: List[Dict[str, Any]] = Field(default_factory=list)
    semantic_conflicts: List[Dict[str, Any]] = Field(default_factory=list)
    doc_conflicts: List[Dict[str, Any]] = Field(default_factory=list)
    
    summary: str = ""
    breaking_changes_count: int = 0
    compatibility_score: Optional[float] = None
    
    status: str = "pending"  # pending, completed, failed
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        arbitrary_types_allowed = True