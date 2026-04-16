from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field, validator
from bson import ObjectId
from core_ai.models.codefile import PyObjectId

class AnalysisResult(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    code_file_id: PyObjectId = Field(alias="code_file_id")  # ربط بنموذج CodeFile
    analysis_started_at: datetime = Field(default_factory=datetime.utcnow, alias="analysis_started_at")
    analysis_completed_at: Optional[datetime] = Field(default=None, alias="analysis_completed_at")
    status: str = Field(default="IN_PROGRESS", alias="status")  # IN_PROGRESS, COMPLETED, FAILED
    ast_structure: Optional[Dict[str, Any]] = Field(default=None, alias="ast_structure")
    extracted_features: Optional[Dict[str, Any]] = Field(default=None, alias="extracted_features")
    dependencies: Optional[List[str]] = Field(default=None, alias="dependencies")
    dependency_graph: Optional[Dict[str, Any]] = Field(default=None, alias="dependency_graph")
    semantic_analysis_data: Optional[Dict[str, Any]] = Field(default=None, alias="semantic_analysis_data")
    # يقبل Dict أو String للتوافق مع البيانات القديمة
    class_diagram_data: Optional[Union[Dict[str, Any], str]] = Field(default=None, alias="class_diagram_data")

    class Config:
        allow_population_by_field_name = True # تم تغيير هذا
        validate_by_name = True # استخدم هذا بدلاً منه
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

    @validator('class_diagram_data', pre=True, always=True)
    def validate_class_diagram_data(cls, v):
        """تحويل البيانات القديمة من String إلى Dict تلقائياً"""
        import json

        if v is None:
            return None

        if isinstance(v, dict):
            # البيانات بالفعل Dict - رائع!
            return v

        if isinstance(v, str):
            try:
                # البيانات القديمة كـ String - نحولها لـ Dict
                # تنظيف علامات الاقتباس المفردة وتحويلها لـ JSON
                sanitized = v.replace("'", '"')
                return json.loads(sanitized)
            except (json.JSONDecodeError, ValueError) as e:
                print(f"⚠️  تحذير: فشل تحويل class_diagram_data من String: {e}")
                print(f"📄 المحتوى: {v[:100]}...")
                # بدلاً من الفشل، نعيد قاموس فارغ
                return {}

        # نوع غير متوقع - نعيد قاموس فارغ
        print(f"⚠️  تحذير: نوع غير متوقع لـ class_diagram_data: {type(v)}")
        return {}


class AnalysisJob(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    code_file_id: PyObjectId = Field(alias="code_file_id")  # ربط بنموذج CodeFile
    status: str = Field(default="CREATED", alias="status")  # CREATED, STARTED, COMPLETED, FAILED
    created_at: datetime = Field(default_factory=datetime.utcnow, alias="created_at")
    started_at: Optional[datetime] = Field(default=None, alias="started_at")
    completed_at: Optional[datetime] = Field(default=None, alias="completed_at")
    error_message: Optional[str] = Field(default=None, alias="error_message")

    class Config:
        allow_population_by_field_name = True # تم تغيير هذا
        validate_by_name = True # استخدم هذا بدلاً منه
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
