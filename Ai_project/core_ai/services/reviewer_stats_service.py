import logging
from datetime import datetime, timedelta
from functools import wraps
from typing import Dict, Optional, Any, List
import re

from django.conf import settings
from django.core.cache import cache
from celery import current_app
from core_ai.mongo_utils import get_mongo_db

logger = logging.getLogger(__name__)


def cached(key: str, timeout: int = 60):
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            cached_value = cache.get(key)
            if cached_value is not None:
                logger.info(f"Cache hit for key: {key}")
                return cached_value
            value = func(self, *args, **kwargs)
            if value is not None:
                cache.set(key, value, timeout)
                logger.info(f"Cache set for key: {key} with timeout: {timeout}s")
            return value
        return wrapper
    return decorator


class ReviewerStatsService:
    def __init__(self):
        self.db = get_mongo_db()
        if self.db is None:
            logger.error("MongoDB connection failed in ReviewerStatsService")

    def _get_collection(self, collection_name: str):
        if self.db is None:
            return None
        return self.db[collection_name]

    @cached("stats_throughput_24h", timeout=60)
    def get_throughput_24h(self) -> Optional[Dict[str, Any]]:
        try:
            collection = self._get_collection(settings.ANALYSIS_RESULTS_COLLECTION)
            if collection is None:
                logger.error("Failed to get analysis_results collection")
                return None

            now = datetime.utcnow()
            twenty_four_hours_ago = now - timedelta(hours=24)

            pipeline = [
                {
                    "$match": {
                        "status": "COMPLETED",
                        "analysis_completed_at": {
                            "$gte": twenty_four_hours_ago,
                            "$lte": now
                        }
                    }
                },
                {
                    "$group": {
                        "_id": None,
                        "count": {"$sum": 1},
                        "avg_processing_time": {
                            "$avg": {
                                "$subtract": ["$analysis_completed_at", "$analysis_started_at"]
                            }
                        }
                    }
                }
            ]

            result = list(collection.aggregate(pipeline))
            if result:
                data = result[0]
                return {
                    "throughput_24h": data.get("count", 0),
                    "avg_processing_time_ms": int(data.get("avg_processing_time", 0) / 1000000) if data.get("avg_processing_time") else 0
                }
            return {"throughput_24h": 0, "avg_processing_time_ms": 0}
        except Exception as e:
            logger.error(f"Error calculating throughput_24h: {str(e)}")
            return None

    @cached("stats_avg_queue_time", timeout=60)
    def get_avg_queue_time(self) -> Optional[Dict[str, Any]]:
        try:
            collection = self._get_collection(settings.ANALYSIS_JOBS_COLLECTION)
            if collection is None:
                logger.error("Failed to get analysis_jobs collection")
                return None

            pipeline = [
                {
                    "$match": {
                        "started_at": {"$exists": True},
                        "created_at": {"$exists": True}
                    }
                },
                {
                    "$group": {
                        "_id": None,
                        "avg_queue_time": {
                            "$avg": {
                                "$subtract": ["$started_at", "$created_at"]
                            }
                        },
                        "max_queue_time": {
                            "$max": {
                                "$subtract": ["$started_at", "$created_at"]
                            }
                        },
                        "min_queue_time": {
                            "$min": {
                                "$subtract": ["$started_at", "$created_at"]
                            }
                        }
                    }
                }
            ]

            result = list(collection.aggregate(pipeline))
            if result:
                data = result[0]
                return {
                    "avg_queue_time_ms": int(data.get("avg_queue_time", 0) / 1000000) if data.get("avg_queue_time") else 0,
                    "max_queue_time_ms": int(data.get("max_queue_time", 0) / 1000000) if data.get("max_queue_time") else 0,
                    "min_queue_time_ms": int(data.get("min_queue_time", 0) / 1000000) if data.get("min_queue_time") else 0
                }
            return {"avg_queue_time_ms": 0, "max_queue_time_ms": 0, "min_queue_time_ms": 0}
        except Exception as e:
            logger.error(f"Error calculating avg_queue_time: {str(e)}")
            return None

    @cached("stats_avg_duration_by_lang", timeout=30)
    def get_avg_duration_by_lang(self) -> Optional[Dict[str, Any]]:
        try:
            code_files_collection = self._get_collection(settings.CODE_FILES_COLLECTION)
            analysis_results_collection = self._get_collection(settings.ANALYSIS_RESULTS_COLLECTION)

            if code_files_collection is None or analysis_results_collection is None:
                logger.error("Failed to get required collections")
                return None

            pipeline = [
                {
                    "$match": {
                        "status": "COMPLETED",
                        "analysis_completed_at": {"$exists": True},
                        "analysis_started_at": {"$exists": True}
                    }
                },
                {
                    "$lookup": {
                        "from": settings.CODE_FILES_COLLECTION,
                        "localField": "code_file_id",
                        "foreignField": "_id",
                        "as": "code_file"
                    }
                },
                {
                    "$unwind": {
                        "path": "$code_file",
                        "preserveNullAndEmptyArrays": True
                    }
                },
                {
                    "$group": {
                        "_id": "$code_file.file_type",
                        "avg_duration": {
                            "$avg": {
                                "$subtract": ["$analysis_completed_at", "$analysis_started_at"]
                            }
                        },
                        "count": {"$sum": 1}
                    }
                },
                {
                    "$sort": {"_id": 1}
                }
            ]

            result = list(analysis_results_collection.aggregate(pipeline))
            by_lang = {}
            for item in result:
                file_type = item.get("_id") or "unknown"
                by_lang[file_type] = {
                    "avg_duration_ms": int(item.get("avg_duration", 0) / 1000000) if item.get("avg_duration") else 0,
                    "count": item.get("count", 0)
                }
            return {"by_language": by_lang}
        except Exception as e:
            logger.error(f"Error calculating avg_duration_by_lang: {str(e)}")
            return None

    @cached("stats_verifier_stats", timeout=60)
    def get_verifier_stats(self) -> Optional[Dict[str, Any]]:
        try:
            collection = self._get_collection(settings.AI_EXPLANATIONS_COLLECTION)
            if collection is None:
                logger.error("Failed to get ai_explanations collection")
                return None

            pipeline = [
                {
                    "$group": {
                        "_id": "$exp_type",
                        "total": {"$sum": 1},
                        "verifier_fallbacks": {
                            "$sum": {"$cond": ["$verifier_fallback", 1, 0]}
                        },
                        "verifier_success": {
                            "$sum": {"$cond": [{"$eq": ["$verifier_fallback", False]}, 1, 0]}
                        }
                    }
                },
                {"$sort": {"_id": 1}}
            ]

            result = list(collection.aggregate(pipeline))
            breakdown = {}
            total_all = 0
            fallbacks_all = 0
            for item in result:
                exp_type = item.get("_id") or "unknown"
                total = item.get("total", 0)
                fallbacks = item.get("verifier_fallbacks", 0)
                total_all += total
                fallbacks_all += fallbacks
                breakdown[exp_type] = {
                    "total": total,
                    "verifier_success": item.get("verifier_success", 0),
                    "verifier_fallbacks": fallbacks,
                    "fallback_rate_percent": round(fallbacks / total * 100, 2) if total > 0 else 0
                }

            return {
                "by_type": breakdown,
                "overall": {
                    "total_explanations": total_all,
                    "verifier_fallbacks": fallbacks_all,
                    "fallback_rate_percent": round(fallbacks_all / total_all * 100, 2) if total_all > 0 else 0
                }
            }
        except Exception as e:
            logger.error(f"Error calculating verifier_stats: {str(e)}")
            return None

    
    @cached("stats_error_classification", timeout=60)
    def get_error_classification(self) -> Optional[Dict[str, Any]]:
        try:
            collection = self._get_collection(settings.ANALYSIS_JOBS_COLLECTION)
            if collection is None:
                logger.error("Failed to get analysis_jobs collection")
                return None

            pipeline = [
                {
                    "$match": {
                        "status": "FAILED",
                        "error_message": {"$exists": True, "$ne": None}
                    }
                },
                {
                    "$group": {
                        "_id": {
                            "$switch": {
                                "branches": [
                                    {"case": {"$regexMatch": {"input": "$error_message", "regex": "syntax", "options": "i"}}, "then": "SyntaxError"},
                                    {"case": {"$regexMatch": {"input": "$error_message", "regex": "timeout", "options": "i"}}, "then": "TimeoutError"},
                                    {"case": {"$regexMatch": {"input": "$error_message", "regex": "memory", "options": "i"}}, "then": "MemoryError"},
                                    {"case": {"$regexMatch": {"input": "$error_message", "regex": "model|ai", "options": "i"}}, "then": "AIModelError"},
                                ],
                                "default": "Unknown"
                            }
                        },
                        "count": {"$sum": 1}
                    }
                }
            ]

            result = list(collection.aggregate(pipeline))
            error_classification = {item["_id"]: item["count"] for item in result}
            total_failed = sum(error_classification.values())

            return {
                "total_failed": total_failed,
                "error_classification": error_classification
            }
        except Exception as e:
            logger.error(f"Error calculating error_classification: {str(e)}")
            return None

    @cached("stats_size_distribution", timeout=60)
    def get_size_distribution(self) -> Optional[Dict[str, Any]]:
        try:
            collection = self._get_collection(settings.CODE_FILES_COLLECTION)
            if collection is None:
                logger.error("Failed to get code_files collection")
                return None

            pipeline = [
                {
                    # استخدم file_size مباشرة إذا موجود، وإلا احسب من content إذا موجود
                    "$addFields": {
                        "content_length": {
                            "$cond": {
                                "if": {"$gt": ["$file_size", None]},
                                "then": "$file_size",
                                "else": {
                                    "$cond": {
                                        "if": {"$and": [
                                            {"$gt": ["$content", None]},
                                            {"$eq": [{"$type": "$content"}, "string"]}
                                        ]},
                                        "then": {"$strLenCP": "$content"},
                                        "else": 0
                                    }
                                }
                            }
                        }
                    }
                },
                {
                    "$group": {
                        "_id": {
                            "$cond": [
                                {"$lt": ["$content_length", 51200]},
                                "under_50KB",
                                {
                                    "$cond": [
                                        {"$lt": ["$content_length", 204800]},
                                        "50_to_200KB",
                                        "over_200KB"
                                    ]
                                }
                            ]
                        },
                        "count": {"$sum": 1},
                        "avg_size": {"$avg": "$content_length"},
                        "max_size": {"$max": "$content_length"}
                    }
                },
                {
                    "$sort": {"_id": 1}
                }
            ]

            result = list(collection.aggregate(pipeline))
            distribution = {
                "under_50KB": 0,
                "50_to_200KB": 0,
                "over_200KB": 0
            }

            for item in result:
                size_bucket = item.get("_id", "unknown")
                if size_bucket in distribution:
                    distribution[size_bucket] = item.get("count", 0)

            return {
                "size_distribution": distribution,
                "details": [
                    {
                        "bucket": item.get("_id"),
                        "count": item.get("count", 0),
                        "avg_size_bytes": round(item.get("avg_size", 0), 0),
                        "max_size_bytes": item.get("max_size", 0)
                    }
                    for item in result
                ]
            }
        except Exception as e:
            logger.error(f"Error calculating size_distribution: {str(e)}")
            return None

    @cached("stats_generated_files", timeout=60)
    def get_generated_files_stats(self) -> Optional[Dict[str, Any]]:
        try:
            collection = self._get_collection(settings.GENERATED_FILES_COLLECTION)
            if collection is None:
                logger.error("Failed to get generated_files collection")
                return None

            pipeline = [
                {
                    "$group": {
                        "_id": "$file_type",
                        "count": {"$sum": 1},
                        "avg_size": {"$avg": "$file_size"},
                        "max_size": {"$max": "$file_size"},
                        "total_downloads": {"$sum": "$downloaded_count"}
                    }
                },
                {
                    "$sort": {"_id": 1}
                }
            ]

            result = list(collection.aggregate(pipeline))
            files_stats = {}
            for item in result:
                file_type = item.get("_id") or "unknown"
                files_stats[file_type] = {
                    "count": item.get("count", 0),
                    "avg_size_bytes": round(item.get("avg_size", 0), 0),
                    "max_size_bytes": item.get("max_size", 0),
                    "total_downloads": item.get("total_downloads", 0)
                }

            return {"generated_files_breakdown": files_stats}
        except Exception as e:
            logger.error(f"Error calculating generated_files_stats: {str(e)}")
            return None

    @cached("stats_celery_health", timeout=60)
    def get_celery_health(self) -> Optional[Dict[str, Any]]:
        try:
            inspector = current_app.control.inspect(timeout=2.0)
            if inspector is None:
                logger.error("Failed to get Celery inspector")
                return None

            active_tasks = inspector.active() or {}
            reserved_tasks = inspector.reserved() or {}

            active_count = sum(len(tasks) for tasks in active_tasks.values())
            reserved_count = sum(len(tasks) for tasks in reserved_tasks.values())

            collection = self._get_collection(settings.AI_TASKS_COLLECTION)
            if collection is None:
                retry_count = 0
            else:
                try:
                    retry_count = collection.count_documents({"status": "failed", "retried": True})
                except Exception as e:
                    logger.warning(f"Failed to count retried tasks: {str(e)}")
                    retry_count = 0

            return {
                "active_tasks": active_count,
                "reserved_tasks": reserved_count,
                "retried_tasks": retry_count,
                "status": "healthy" if active_count >= 0 else "unhealthy"
            }
        except Exception as e:
            logger.error(f"Error calculating celery_health: {str(e)}")
            return None

    def get_all_stats(self) -> Dict[str, Any]:
        try:
            throughput = self.get_throughput_24h()
            queue_time = self.get_avg_queue_time()
            duration_by_lang = self.get_avg_duration_by_lang()
            verifier_stats = self.get_verifier_stats()
            error_classification = self.get_error_classification()
            size_distribution = self.get_size_distribution()
            generated_files = self.get_generated_files_stats()
            celery_health = self.get_celery_health()

            return {
                "performance": {
                    "throughput_24h": throughput.get("throughput_24h") if throughput else None,
                    "avg_processing_time_ms": throughput.get("avg_processing_time_ms") if throughput else None,
                    "avg_queue_time_ms": queue_time.get("avg_queue_time_ms") if queue_time else None,
                    "duration_by_language": duration_by_lang.get("by_language") if duration_by_lang else None,
                    "status": "ok" if throughput and queue_time else "degraded"
                },
                "quality": {
                    "verifier_stats": verifier_stats if verifier_stats else None,
                    "error_classification": error_classification if error_classification else None,
                    "status": "ok" if verifier_stats else "degraded"
                },
                "files": {
                    "size_distribution": size_distribution.get("size_distribution") if size_distribution else None,
                    "generated_files": generated_files.get("generated_files_breakdown") if generated_files else None,
                    "status": "ok" if size_distribution and generated_files else "degraded"
                },
                "celery": celery_health if celery_health else {"status": "unavailable"},
                "timestamp": datetime.utcnow().isoformat(),
                "overall_status": "healthy"
            }
        except Exception as e:
            logger.error(f"Error in get_all_stats: {str(e)}")
            return {
                "performance": {"status": "AI service unavailable"},
                "quality": {"status": "AI service unavailable"},
                "files": {"status": "AI service unavailable"},
                "celery": {"status": "unavailable"},
                "timestamp": datetime.utcnow().isoformat(),
                "overall_status": "unhealthy",
                "error": str(e)
            }
