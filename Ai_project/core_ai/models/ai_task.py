from typing import Optional, Any , Union
from datetime import datetime
from pydantic import BaseModel, Field
from bson import ObjectId
from core_ai.models.codefile import PyObjectId


class AITask(BaseModel):
    """
    نموذج بيانات لمهام الذكاء الاصطناعي
    يُستخدم لإدارة مهام المعالجة في الخلفية
    """
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    task_id: str               # معرف المهمة الفريد من Celery
    analysis_id: Union[PyObjectId, str]    # ربط بـ AnalysisResult او Project
    exp_type: Optional[str] = Field(default=None)  # نوع التحليل ('class_diagram', 'explanation')
    explain_level: Optional[str] = Field(default=None)  # مستوى الشرح ('high_level', 'low_level')
    status: str = Field(default="pending")  # pending, processing, completed, failed
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = Field(default=None)
    result: Optional[Any] = Field(default=None)  # نتيجة المهمة
    error: Optional[str] = Field(default=None)    # رسالة خطأ إذا فشلت

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

    @staticmethod
    def get_by_task_id(task_id):
        """
        البحث عن مهمة واحدة بواسطة task_id
        مثال: task = AITask.get_by_task_id("abc-123")
        """
        import logging
        logger = logging.getLogger(__name__)
        
        from core_ai.mongo_utils import get_mongo_db
        
        db = get_mongo_db()
        if db is None:
            logger.error("Failed to get MongoDB connection")
            return None

        logger.info(f"Searching for AITask with task_id: {task_id}")
        data = db['ai_tasks'].find_one({"task_id": task_id})
        if data:
            logger.info(f"Found AITask: {data}")
            return AITask(**data)
        else:
            logger.warning(f"AITask not found for task_id: {task_id}")
        return None

    @staticmethod
    def get_user_tasks(analysis_id=None, limit=50):
        """
        الحصول على قائمة المهام مع فلترة اختيارية
        مثال: tasks = AITask.get_user_tasks("analysis-123")
        """
        from core_ai.mongo_utils import get_mongo_db
        
        db = get_mongo_db()
        if db is None:
            return []

        query = {}
        if analysis_id:
            query["analysis_id"] = analysis_id

        tasks_data = list(
            db['ai_tasks']
            .find(query)
            .sort("created_at", -1)
            .limit(limit)
        )

        return [AITask(**data) for data in tasks_data]
