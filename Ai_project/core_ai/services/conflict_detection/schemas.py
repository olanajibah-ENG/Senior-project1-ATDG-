from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from enum import Enum

# --- 1. Enums للتحكم الدقيق ---
class AnalysisType(str, Enum):
    CODE_VS_CODE = "code_vs_code"
    CODE_VS_DOC = "code_vs_doc"
    FULL = "full_analysis"

class ChangeType(str, Enum):
    BREAKING_CHANGE = "breaking_change"
    BEHAVIOR_CHANGE = "behavior_change"
    REFACTORING = "refactoring"
    DOC_DRIFT = "documentation_drift"
    UNUSED_CODE = "unused_code"
    NEW_FEATURE = "new_feature"

class SeverityLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

class DocType(str, Enum):
    HIGH_LEVEL = "high"
    LOW_LEVEL = "low"
    UNKNOWN = "unknown"

# --- 2. الهيكل الموحد للكلاسات ---
class MethodDetail(BaseModel):
    name: str
    signature: str
    is_abstract: bool = False
    is_constructor: bool = False
    visibility: str = "public"
    is_override: bool = False

class AttributeDetail(BaseModel):
    name: str
    type: str = "any"
    visibility: str = "public"

class ClassDetail(BaseModel):
    name: str
    type: str
    methods: List[MethodDetail] = Field(default_factory=list)
    attributes: List[AttributeDetail] = Field(default_factory=list)
    relationships: List[Dict[str, Any]] = Field(default_factory=list)
    is_generic: bool = False
    is_abstract: bool = False
    is_interface: bool = False

class UnifiedClassDiagram(BaseModel):
    classes: List[ClassDetail] = Field(default_factory=list)
    relationships: List[Dict[str, Any]] = Field(default_factory=list)
    language: str = ""
    project_id: Optional[str] = None

# --- 3. عناصر التناقض المحسنة ---
class ConflictItem(BaseModel):
    type: ChangeType
    severity: SeverityLevel
    class_name: str
    member: Optional[str] = None
    description: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    recommendation: Optional[str] = None
    confidence: float = 0.0
    doc_type: Optional[DocType] = None  # ✅ جديد: لتحديد مصدر التناقض

# --- 4. النتيجة النهائية ---
class ConflictAnalysisResult(BaseModel):
    analysis_type: AnalysisType  # ✅ تحسين: استخدام Enum
    version_a: str
    version_b: Optional[str] = None

    diagram_a: UnifiedClassDiagram
    diagram_b: Optional[UnifiedClassDiagram] = None

    structural_conflicts: List[ConflictItem] = Field(default_factory=list)
    semantic_conflicts: List[ConflictItem] = Field(default_factory=list)
    doc_conflicts: List[ConflictItem] = Field(default_factory=list)

    summary: str = ""
    breaking_changes_count: int = 0
    compatibility_score: Optional[float] = None