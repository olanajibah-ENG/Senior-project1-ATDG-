from typing import Optional, List, Dict, Any, Union
from datetime import datetime
import json
from pydantic import BaseModel, Field, field_validator
from bson import ObjectId
from core_ai.models.codefile import PyObjectId


class AnalysisResult(BaseModel):
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
    }

    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    code_file_id: PyObjectId = Field(alias="code_file_id")
    analysis_started_at: datetime = Field(default_factory=datetime.utcnow, alias="analysis_started_at")
    analysis_completed_at: Optional[datetime] = Field(default=None, alias="analysis_completed_at")
    status: str = Field(default="IN_PROGRESS", alias="status")
    ast_structure: Optional[Dict[str, Any]] = Field(default=None, alias="ast_structure")
    extracted_features: Optional[Dict[str, Any]] = Field(default=None, alias="extracted_features")
    dependencies: Optional[List[str]] = Field(default=None, alias="dependencies")
    dependency_graph: Optional[Dict[str, Any]] = Field(default=None, alias="dependency_graph")
    semantic_analysis_data: Optional[Dict[str, Any]] = Field(default=None, alias="semantic_analysis_data")
    class_diagram_data: Optional[Union[Dict[str, Any], str]] = Field(default=None, alias="class_diagram_data")

    @field_validator("class_diagram_data", mode="before")
    @classmethod
    def validate_class_diagram_data(cls, v: Any) -> Optional[Dict[str, Any]]:
        """تحويل البيانات القديمة من String إلى Dict تلقائياً"""
        if v is None:
            return None
        if isinstance(v, dict):
            return v
        if isinstance(v, str):
            try:
                sanitized = v.replace("'", '"')
                return json.loads(sanitized)
            except (json.JSONDecodeError, ValueError) as e:
                print(f"⚠️  تحذير: فشل تحويل class_diagram_data من String: {e}")
                return {}
        print(f"⚠️  تحذير: نوع غير متوقع لـ class_diagram_data: {type(v)}")
        return {}


class AnalysisJob(BaseModel):
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
    }

    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    code_file_id: PyObjectId = Field(alias="code_file_id")
    status: str = Field(default="CREATED", alias="status")
    created_at: datetime = Field(default_factory=datetime.utcnow, alias="created_at")
    started_at: Optional[datetime] = Field(default=None, alias="started_at")
    completed_at: Optional[datetime] = Field(default=None, alias="completed_at")
    error_message: Optional[str] = Field(default=None, alias="error_message")
