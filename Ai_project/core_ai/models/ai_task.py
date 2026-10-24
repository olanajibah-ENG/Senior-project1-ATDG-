from typing import Optional, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field
from bson import ObjectId
from core_ai.models.codefile import PyObjectId


class AITask(BaseModel):
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
    }

    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    task_id: str
    analysis_id: Union[PyObjectId, str]
    exp_type: Optional[str] = Field(default=None)
    explain_level: Optional[str] = Field(default=None)
    status: str = Field(default="pending")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = Field(default=None)
    result: Optional[Any] = Field(default=None)
    error: Optional[str] = Field(default=None)

    @staticmethod
    def get_by_task_id(task_id: str) -> Optional["AITask"]:
        import logging
        logger = logging.getLogger(__name__)
        from core_ai.mongo_utils import get_mongo_db

        db = get_mongo_db()
        if db is None:
            logger.error("Failed to get MongoDB connection")
            return None

        logger.info(f"Searching for AITask with task_id: {task_id}")
        data = db["ai_tasks"].find_one({"task_id": task_id})
        if data:
            return AITask(**data)
        logger.warning(f"AITask not found for task_id: {task_id}")
        return None

    @staticmethod
    def get_user_tasks(analysis_id: Optional[str] = None, limit: int = 50):
        from core_ai.mongo_utils import get_mongo_db

        db = get_mongo_db()
        if db is None:
            return []

        query = {}
        if analysis_id:
            query["analysis_id"] = analysis_id

        tasks_data = list(
            db["ai_tasks"].find(query).sort("created_at", -1).limit(limit)
        )
        return [AITask(**data) for data in tasks_data]
