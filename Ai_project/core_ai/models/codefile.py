from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, Field, field_validator, GetCoreSchemaHandler
from pydantic_core import core_schema
from bson import ObjectId


class PyObjectId(ObjectId):
    """ObjectId compatible with pydantic v2."""

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        return core_schema.no_info_plain_validator_function(
            cls._validate,
            serialization=core_schema.to_string_ser_schema(),
        )

    @classmethod
    def _validate(cls, value: Any) -> ObjectId:
        if isinstance(value, ObjectId):
            return value
        if not ObjectId.is_valid(value):
            raise ValueError(f"Invalid ObjectId: {value!r}")
        return ObjectId(value)

    @classmethod
    def __get_validators__(cls):
        # pydantic v1 compat shim (used by older serializers)
        yield cls._validate


class CodeFile(BaseModel):
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
    }

    id: Optional[PyObjectId] = Field(default=None, alias="_id")

    # ── معلومات الملف الأساسية ─────────────────────────────────────────────
    filename: str
    file_type: str
    file_hash: Optional[str] = None

    # ── التخزين — GridFS ───────────────────────────────────────────────────
    gridfs_id: Optional[str] = None
    file_size: Optional[int] = None

    # ── الإصدارات ─────────────────────────────────────────────────────────
    version_number: int = 1
    parent_codefile_id: Optional[PyObjectId] = None
    is_delta: bool = False

    # ── ربط بالمشروع ──────────────────────────────────────────────────────
    source_project_id: Optional[str] = None
    project_version: Optional[int] = None

    # ── الحالة ────────────────────────────────────────────────────────────
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    analysis_status: str = "PENDING"

    # ── معلومات المستخدم ──────────────────────────────────────────────────
    user_email: Optional[str] = None
    user_name: Optional[str] = None
    project_name: Optional[str] = None
