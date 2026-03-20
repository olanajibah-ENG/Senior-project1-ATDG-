"""
Evaluation model for storing explanation evaluation results
"""

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

try:
    from pydantic.json import ENCODERS_BY_TYPE
except ImportError:
    from pydantic.v1.json import ENCODERS_BY_TYPE


class EvaluationResult(BaseModel):
    """Model for storing evaluation results"""
    
    id: Optional[str] = Field(default=None, alias="_id")
    explanation_id: str = Field(..., description="ID of the evaluated explanation")
    layer3_method: str = Field(default="rule_based", description="llm or rule_based")
    human_reviewed: bool = Field(default=False, description="Whether human review was submitted")
    
    # Layer results
    layer1: Dict[str, Any] = Field(..., description="Layer 1: AST Cross-Check results")
    layer2: Dict[str, Any] = Field(..., description="Layer 2: Completeness Check results")
    layer3: Dict[str, Any] = Field(..., description="Layer 3: LLM-as-a-Judge results")
    layer4: Dict[str, Any] = Field(..., description="Layer 4: Human Reviewer results")
    
    # Final results
    final_score: float = Field(..., ge=0.0, le=1.0, description="Final evaluation score")
    final_score_percentage: float = Field(..., ge=0.0, le=100.0, description="Final score as percentage")
    overall_verdict: str = Field(..., description="Overall verdict (EXCELLENT, GOOD, ACCEPTABLE, POOR)")
    
    # Metadata
    evaluated_at: datetime = Field(default_factory=datetime.utcnow)
    evaluation_duration: Optional[float] = Field(None)
    
    class Config:
        collection = "explanation_evaluations"
        json_encoders = {datetime: lambda v: v.isoformat()}


class HumanFeedback(BaseModel):
    """Model for storing human feedback on explanations"""
    
    id: Optional[str] = Field(default=None, alias="_id")
    explanation_id: str = Field(..., description="ID of the explanation being reviewed")
    reviewer_id: Optional[str] = Field(None)
    score: float = Field(..., ge=0.0, le=1.0, description="Human reviewer score 0.0-1.0")
    comment: Optional[str] = Field(None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        collection = "human_feedback"
        json_encoders = {datetime: lambda v: v.isoformat()}


class EvaluationStats(BaseModel):
    """Model for evaluation statistics"""
    
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
    
    class Config:
        collection = "evaluation_stats"
        json_encoders = {datetime: lambda v: v.isoformat()}