"""
نموذج شروحات الذكاء الاصطناعي (AI Explanations)
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field
from bson import ObjectId
from core_ai.models.codefile import PyObjectId


class GeneratedFile(BaseModel):
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
    }

    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    explanation_id: PyObjectId
    filename: str
    file_type: str
    file_content: bytes
    file_size: int
    created_at: datetime = Field(default_factory=datetime.utcnow)
    downloaded_count: int = Field(default=0)


class AIExplanation(BaseModel):
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
    }

    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    analysis_id: PyObjectId
    explanation_type: str
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
