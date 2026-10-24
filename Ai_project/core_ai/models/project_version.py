from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from bson import ObjectId
from core_ai.models.codefile import PyObjectId


class ProjectVersion(BaseModel):
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
    }

    id: Optional[PyObjectId] = Field(default=None, alias="_id")

    project_id: str
    project_name: Optional[str] = None
    version_number: int = 1
    created_at: datetime = Field(default_factory=datetime.utcnow)

    file_ids: List[str] = []
    delta_file_ids: List[str] = []

    change_summary: Optional[str] = None
    total_files: int = 0
    new_files: int = 0
    modified_files: int = 0
    unchanged_files: int = 0
