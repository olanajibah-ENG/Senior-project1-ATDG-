"""
models/project_version.py
==========================
نموذج إصدارات المشروع في MongoDB.

كل إصدار يحفظ قائمة الـ file_ids اللي تشكّل هاد الإصدار.
الملفات اللي ما تغيرت بين الإصدارات تُشار لها بنفس الـ id بدون تخزين جديد.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from bson import ObjectId
from core_ai.models.codefile import PyObjectId


class ProjectVersion(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")

    # ── معلومات الإصدار ────────────────────────────────────────────────────
    project_id: str                          # UUID للمشروع
    project_name: Optional[str] = None
    version_number: int = 1                  # 1, 2, 3...
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # ── الملفات — Content Addressing ──────────────────────────────────────
    # قائمة بكل file_ids اللي تشكّل هاد الإصدار
    # الملفات اللي ما تغيرت بتشير لنفس الـ id من الإصدار السابق
    file_ids: List[str] = []

    # ── Delta — للملفات اللي تغيرت فقط ───────────────────────────────────
    # file_ids اللي هي deltas مش snapshots كاملة
    delta_file_ids: List[str] = []

    # ── معلومات إضافية ────────────────────────────────────────────────────
    change_summary: Optional[str] = None     # وصف التغييرات
    total_files: int = 0
    new_files: int = 0                       # ملفات جديدة بهاد الإصدار
    modified_files: int = 0                  # ملفات اتعدلت
    unchanged_files: int = 0                 # ملفات ما اتغيرت

    class Config:
        validate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}