"""
نموذج شروحات الذكاء الاصطناعي (AI Explanations)
هذا نموذج Pydantic للتحقق من صحة البيانات والتحويل (DTO/Schema)
لا يحتوي على database operations - فقط تعريف البيانات
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field
from bson import ObjectId
from core_ai.models.codefile import PyObjectId


class GeneratedFile(BaseModel):
    """
    نموذج بيانات للملفات المولدة (PDF و Markdown)
    يُستخدم لحفظ الملفات المولدة في قاعدة البيانات
    """
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    explanation_id: PyObjectId  # ربط بـ AIExplanation
    filename: str              # اسم الملف
    file_type: str             # 'pdf' أو 'markdown'
    file_content: bytes        # محتوى الملف (binary)
    file_size: int             # حجم الملف بالبايت
    created_at: datetime = Field(default_factory=datetime.utcnow)
    downloaded_count: int = Field(default=0)  # عدد مرات التحميل

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class AIExplanation(BaseModel):
    """
    نموذج بيانات للشروحات المولدة من الذكاء الاصطناعي
    يُستخدم للتحقق من صحة البيانات والتحويل بين JSON و Python objects
    """
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    analysis_id: PyObjectId  # ربط بـ AnalysisResult
    explanation_type: str    # 'high_level' أو 'low_level' أو 'technical_report'
    content: str             # نص الشرح الناتج من AI
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}