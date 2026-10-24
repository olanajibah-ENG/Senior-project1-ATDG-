"""
Evaluation model for storing explanation evaluation results
"""
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class EvaluationResult(BaseModel):
    model_config = {
        "populate_by_name": True,
    }

    id: Optional[str] = Field(default=None, alias="_id")
    explanation_id: str = Field(..., description="ID of the evaluated explanation")
    layer3_method: str = Field(default="rule_based")
    human_reviewed: bool = Field(default=False)

    layer1: Dict[str, Any] = Field(...)
    layer2: Dict[str, Any] = Field(...)
    layer3: Dict[str, Any] = Field(...)
    layer4: Dict[str, Any] = Field(...)

    final_score: float = Field(..., ge=0.0, le=1.0)
    final_score_percentage: float = Field(..., ge=0.0, le=100.0)
    overall_verdict: str = Field(...)

    evaluated_at: datetime = Field(default_factory=datetime.utcnow)
    evaluation_duration: Optional[float] = Field(None)


class HumanFeedback(BaseModel):
    model_config = {
        "populate_by_name": True,
    }

    id: Optional[str] = Field(default=None, alias="_id")
    explanation_id: str = Field(...)
    reviewer_id: Optional[str] = Field(None)
    score: float = Field(..., ge=0.0, le=1.0)
    comment: Optional[str] = Field(None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class EvaluationStats(BaseModel):
    total_evaluations: int = Field(default=0)
    average_score: float = Field(default=0.0, ge=0.0, le=1.0)
    verdict_distribution: Dict[str, int] = Field(default_factory=dict)
    excellent_count: int = Field(default=0)
    good_count: int = Field(default=0)
    acceptable_count: int = Field(default=0)
    poor_count: int = Field(default=0)
    avg_ast_cross_check: float = Field(default=0.0, ge=0.0, le=1.0)
    avg_completeness: float = Field(default=0.0, ge=0.0, le=1.0)
    avg_llm_judge: float = Field(default=0.0, ge=0.0, le=1.0)
    avg_human_review: Optional[float] = Field(None, ge=0.0, le=1.0)
    last_updated: datetime = Field(default_factory=datetime.utcnow)
