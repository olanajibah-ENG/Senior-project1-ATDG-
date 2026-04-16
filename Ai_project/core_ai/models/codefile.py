from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from bson import ObjectId

try:
    from pydantic.json import ENCODERS_BY_TYPE
except ImportError:
    from pydantic.v1.json import ENCODERS_BY_TYPE


class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, value, values=None, config=None, field=None):
        if not ObjectId.is_valid(value):
            raise ValueError("Invalid ObjectId")
        return ObjectId(value)

    @classmethod
    def modify_schema(cls, field_schema):
        field_schema.update(type="string")


ENCODERS_BY_TYPE[PyObjectId] = str


class CodeFile(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")

    # ── معلومات الملف الأساسية ─────────────────────────────────────────────
    filename: str
    file_type: str                          # 'python', 'java', 'javascript'...
    file_hash: Optional[str] = None         # MD5 hash للتحقق من التكرار

    # ── التخزين — GridFS ───────────────────────────────────────────────────
    # المحتوى يُخزَّن في GridFS، هنا بس نحفظ الـ reference
    gridfs_id: Optional[str] = None         # ObjectId الملف في GridFS
    file_size: Optional[int] = None         # حجم الملف بالـ bytes

    # ── الإصدارات — Delta + Content Addressing ────────────────────────────
    version_number: int = 1                 # رقم الإصدار
    parent_codefile_id: Optional[PyObjectId] = None  # يشير للإصدار السابق
    is_delta: bool = False                  # لو True: gridfs_id يحتوي diff مش محتوى كامل

    # ── ربط بالمشروع ──────────────────────────────────────────────────────
    source_project_id: Optional[str] = None  # UUID للمشروع
    project_version: Optional[int] = None    # رقم إصدار المشروع اللي ينتمي له

    # ── الحالة ────────────────────────────────────────────────────────────
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    analysis_status: str = "PENDING"        # PENDING, IN_PROGRESS, COMPLETED, FAILED

    # ── معلومات المستخدم ──────────────────────────────────────────────────
    user_email: Optional[str] = None
    user_name: Optional[str] = None
    project_name: Optional[str] = None

    class Config:
        validate_by_name = True
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}