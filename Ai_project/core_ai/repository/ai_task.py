
from datetime import datetime
from core_ai.mongo_utils import get_mongo_db
from bson.objectid import ObjectId
from core_ai.models.ai_task import AITask as AITaskModel


class AITaskRepository:
    """
    Repository لإدارة مهام الذكاء الاصطناعي في MongoDB
    مسؤول عن: حفظ المهام، تحديث الحالة، البحث في قاعدة البيانات
    """
    collection_name = 'ai_tasks'

    def __init__(self, task_model: AITaskModel):
        self.task_model = task_model

    def save(self):
        """حفظ المهمة الجديدة في قاعدة البيانات"""
        db = get_mongo_db()
        if db is None:
            raise Exception("تعذر الاتصال بقاعدة البيانات")

        data = self.task_model.dict(by_alias=True, exclude_unset=True)
        if '_id' in data and data['_id'] is None:
            del data['_id']

        result = db[self.collection_name].insert_one(data)
        self.task_model.id = result.inserted_id
        return result.inserted_id

    def update_status(self, status, result=None, error=None):
        """تحديث حالة المهمة الموجودة"""
        import logging
        logger = logging.getLogger(__name__)
        
        db = get_mongo_db()
        if db is None:
            raise Exception("تعذر الاتصال بقاعدة البيانات")

        update_data = {"status": status}

        if result is not None:
            update_data["result"] = result
            update_data["completed_at"] = datetime.utcnow()

        if error is not None:
            update_data["error"] = error
            update_data["completed_at"] = datetime.utcnow()

        # Try to update by _id first, if it exists
        if self.task_model.id:
            logger.info(f"Updating AITask with _id: {self.task_model.id}")
            result = db[self.collection_name].update_one(
                {"_id": self.task_model.id},
                {"$set": update_data}
            )
            logger.info(f"Update result - matched: {result.matched_count}, modified: {result.modified_count}")
        else:
            # Fallback to task_id if _id is not set
            logger.info(f"Updating AITask with task_id: {self.task_model.task_id}")
            result = db[self.collection_name].update_one(
                {"task_id": self.task_model.task_id},
                {"$set": update_data}
            )
            logger.info(f"Update result - matched: {result.matched_count}, modified: {result.modified_count}")

    @classmethod
    def get_by_task_id(cls, task_id):
        """
        البحث عن مهمة واحدة بواسطة task_id
        مثال: task = AITaskRepository.get_by_task_id("abc-123")
        """
        db = get_mongo_db()
        if db is None:
            return None

        data = db[cls.collection_name].find_one({"task_id": task_id})
        if data:
            task_model = AITaskModel(**data)
            return cls(task_model)
        return None

    @classmethod
    def get_user_tasks(cls, analysis_id=None, limit=50):
        """
        الحصول على قائمة المهام مع فلترة اختيارية
        مثال: tasks = AITaskRepository.get_user_tasks("analysis-123")
        """
        db = get_mongo_db()
        if db is None:
            return []

        query = {}
        if analysis_id:
            query["analysis_id"] = analysis_id

        tasks_data = list(
            db[cls.collection_name]
            .find(query)
            .sort("created_at", -1)
            .limit(limit)
        )

        task_repositories = []
        for data in tasks_data:
            task_model = AITaskModel(**data)
            task_repositories.append(cls(task_model))

        return task_repositories

    # Helper methods to access model attributes
    @property
    def task_id(self):
        return self.task_model.task_id

    @property
    def analysis_id(self):
        return self.task_model.analysis_id

    @property
    def exp_type(self):
        return self.task_model.exp_type

    @property
    def status(self):
        return self.task_model.status

    @property
    def created_at(self):
        return self.task_model.created_at

    @property
    def completed_at(self):
        return self.task_model.completed_at

    @property
    def result(self):
        return self.task_model.result

    @property
    def error(self):
        return self.task_model.error
