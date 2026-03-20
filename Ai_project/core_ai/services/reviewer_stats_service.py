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

    @cached("stats_agent_breakdown", timeout=60)
    def get_agent_breakdown(self) -> Optional[Dict[str, Any]]:
        try:
            collection = self._get_collection(settings.AI_TASKS_COLLECTION)
            if collection is None:
                logger.error("Failed to get ai_tasks collection")
                return None

            pipeline = [
                {
                    "$group": {
                        "_id": "$exp_type",
                        "count": {"$sum": 1},
                        "completed": {
                            "$sum": {
                                "$cond": [{"$eq": ["$status", "completed"]}, 1, 0]
                            }
                        },
                        "failed": {
                            "$sum": {
                                "$cond": [{"$eq": ["$status", "failed"]}, 1, 0]
                            }
                        }
                    }
                },
                {
                    "$sort": {"_id": 1}
                }
            ]

            result = list(collection.aggregate(pipeline))
            agents = {}
            for item in result:
                agent_type = item.get("_id") or "unknown"
                total = item.get("count", 0)
                failed = item.get("failed", 0)
                error_rate = (failed / total * 100) if total > 0 else 0
                agents[agent_type] = {
                    "total_tasks": total,
                    "completed": item.get("completed", 0),
                    "failed": failed,
                    "error_rate_percent": round(error_rate, 2)
                }
            return {"agent_breakdown": agents}
        except Exception as e:
            logger.error(f"Error calculating agent_breakdown: {str(e)}")
            return None

    @cached("stats_explanation_quality", timeout=60)
    def get_explanation_quality(self) -> Optional[Dict[str, Any]]:
        try:
            collection = self._get_collection(settings.AI_EXPLANATIONS_COLLECTION)
            if collection is None:
                logger.error("Failed to get ai_explanations collection")
                return None

            pipeline = [
                {
                    "$group": {
                        "_id": "$explanation_type",
                        "count": {"$sum": 1},
                        "avg_content_length": {
                            "$avg": {"$strLenCP": "$content"}
                        },
                        "max_content_length": {
                            "$max": {"$strLenCP": "$content"}
                        },
                        "min_content_length": {
                            "$min": {"$strLenCP": "$content"}
                        }
                    }
                },
                {
                    "$sort": {"_id": 1}
                }
            ]

            result = list(collection.aggregate(pipeline))
            explanations = {}
            for item in result:
                exp_type = item.get("_id") or "unknown"
                explanations[exp_type] = {
                    "count": item.get("count", 0),
                    "avg_content_length": round(item.get("avg_content_length", 0), 2),
                    "max_content_length": item.get("max_content_length", 0),
                    "min_content_length": item.get("min_content_length", 0)
                }
            return {"explanation_breakdown": explanations}
        except Exception as e:
            logger.error(f"Error calculating explanation_quality: {str(e)}")
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
                        "_id": None,
                        "total_failed": {"$sum": 1}
                    }
                }
            ]

            result = list(collection.aggregate(pipeline))
            total_failed = result[0].get("total_failed", 0) if result else 0

            failed_jobs = list(collection.find(
                {"status": "FAILED", "error_message": {"$exists": True}},
                {"error_message": 1}
            ).limit(10000))

            error_patterns = {
                "SyntaxError": 0,
                "TimeoutError": 0,
                "MemoryError": 0,
                "AIModelError": 0,
                "Unknown": 0
            }

            for job in failed_jobs:
                error_msg = job.get("error_message", "")
                if "SyntaxError" in error_msg or "syntax" in error_msg.lower():
                    error_patterns["SyntaxError"] += 1
                elif "TimeoutError" in error_msg or "timeout" in error_msg.lower():
                    error_patterns["TimeoutError"] += 1
                elif "MemoryError" in error_msg or "memory" in error_msg.lower():
                    error_patterns["MemoryError"] += 1
                elif "AIModelError" in error_msg or "model" in error_msg.lower():
                    error_patterns["AIModelError"] += 1
                else:
                    error_patterns["Unknown"] += 1

            return {
                "total_failed": total_failed,
                "error_classification": error_patterns
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
                    "$addFields": {
                        "content_length": {"$strLenCP": "$content"}
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

    @cached("stats_celery_health", timeout=30)
    def get_celery_health(self) -> Optional[Dict[str, Any]]:
        try:
            inspector = current_app.control.inspect()
            if inspector is None:
                logger.error("Failed to get Celery inspector")
                return None

            active_tasks = inspector.active()
            reserved_tasks = inspector.reserved()

            active_count = 0
            if active_tasks:
                active_count = sum(len(tasks) for tasks in active_tasks.values())

            reserved_count = 0
            if reserved_tasks:
                reserved_count = sum(len(tasks) for tasks in reserved_tasks.values())

            collection = self._get_collection(settings.AI_TASKS_COLLECTION)
            if collection is None:
                retry_count = 0
            else:
                try:
                    retry_count = collection.count_documents({
                        "status": "failed",
                        "retried": True
                    })
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
            agent_breakdown = self.get_agent_breakdown()
            explanation_quality = self.get_explanation_quality()
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
                    "agent_breakdown": agent_breakdown.get("agent_breakdown") if agent_breakdown else None,
                    "explanation_breakdown": explanation_quality.get("explanation_breakdown") if explanation_quality else None,
                    "error_classification": error_classification if error_classification else None,
                    "status": "ok" if agent_breakdown and explanation_quality else "degraded"
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
