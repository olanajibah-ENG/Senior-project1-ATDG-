# core_ai/services/conflict_detection/schemas.py
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from enum import Enum
from datetime import datetime


# ─────────────────────────────────────────────────────────────────────────────
# 1. Enums
# ─────────────────────────────────────────────────────────────────────────────

class AnalysisType(str, Enum):
    CODE_VS_CODE = "code_vs_code"
    CODE_VS_DOC  = "code_vs_doc"
    FULL         = "full_analysis"


class ChangeType(str, Enum):
    BREAKING_CHANGE  = "breaking_change"
    BEHAVIOR_CHANGE  = "behavior_change"
    LOGIC_CHANGE     = "logic_change"
    REFACTORING      = "refactoring"
    DOC_DRIFT        = "documentation_drift"
    UNUSED_CODE      = "unused_code"
    NEW_FEATURE      = "new_feature"
    # structural_diff كان بيسأل عنه بـ hasattr، وبدونه كانت إعادة التسمية تنحسب behavior_change
    RENAMED          = "renamed"


class SeverityLevel(str, Enum):
    CRITICAL = "critical"
    HIGH     = "high"
    MEDIUM   = "medium"
    LOW      = "low"
    INFO     = "info"


class DocType(str, Enum):
    HIGH_LEVEL = "high"
    LOW_LEVEL  = "low"
    UNKNOWN    = "unknown"

class ChangeCategory(str, Enum):
    """تصنيف حسب Breaking Changes SLR"""
    SYNTACTIC   = "syntactic"
    SEMANTIC    = "semantic"
    BEHAVIORAL  = "behavioral"


class DocConsistencyLabel(str, Enum):
    """تصنيف DocPrism (LCEF) لعلاقة التوثيق بالكود"""
    CONSISTENT      = "Consistent"
    DIRECT_MISMATCH = "Direct_Mismatch"   # التوثيق بيقول شي، والكود بيعمل شي تاني بداله
    OVER_PROMISE    = "Over_Promise"      # التوثيق بيوعد بشي، والكود ما بيعمله أصلاً
    UNDER_PROMISE   = "Under_Promise"     # الكود بيعمل شي زيادة ما انذكر — ما بينعرض للمستخدم


class ChangeDecision(str, Enum):
    """قرار الـ ChangeClassifier (مصفوفة Signature × Body)"""
    STRUCTURAL_ONLY           = "structural_only"            # التوقيع تغيّر والجسم لا → بدون LLM
    STRUCTURAL_AND_BEHAVIORAL = "structural_and_behavioral"  # التنين تغيّروا
    BEHAVIORAL_CANDIDATE      = "behavioral_candidate"       # الجسم بس تغيّر
    NO_CHANGE                 = "no_change"


class RiskLevel(str, Enum):
    """مخرج الـ SeverityClassifier (من مستويات AexPy). منفصل عن SeverityLevel يلي بتلوّن فيه الواجهة."""
    CRITICAL      = "critical"        # AexPy High
    WARNING       = "warning"         # AexPy Medium / Low
    INFORMATIONAL = "informational"   # AexPy Compatible، أو عنصر اسمه بيبلش بـ _


# ─────────────────────────────────────────────────────────────────────────────
# 2. Input Schema
# ─────────────────────────────────────────────────────────────────────────────

class ConflictRequestInput(BaseModel):
    model_config = {"use_enum_values": True}

    analysis_type: AnalysisType
    project_id:    str
    file_id:       str

    version_a_id: Optional[str] = None
    version_b_id: Optional[str] = None

    version_id:     Optional[str] = None
    doc_version_id: Optional[str] = None


# ─────────────────────────────────────────────────────────────────────────────
# 3. Metadata Schemas
# ─────────────────────────────────────────────────────────────────────────────

class ProjectMetadata(BaseModel):
    project_id:   str
    project_name: str = "Unknown Project"


class FileMetadata(BaseModel):
    file_id:   str
    file_name: str = "Unknown File"
    file_path: str = ""


class VersionMetadata(BaseModel):
    version_id:     str
    version_number: str = ""
    role: str = "reference"


class DocMetadata(BaseModel):
    doc_id:             str
    doc_version_id:     str
    file_name:          str = ""
    type:               str = "high_level"
    linked_to_version:  Optional[str] = None
    auto_fetched:       bool = False


class ConflictMetadata(BaseModel):
    project:       ProjectMetadata
    file:          FileMetadata
    versions:      Optional[Dict[str, VersionMetadata]] = None
    code:          Optional[Dict[str, Any]] = None
    documentation: Optional[DocMetadata]   = None


# ─────────────────────────────────────────────────────────────────────────────
# 4. Diagram Schemas
# ─────────────────────────────────────────────────────────────────────────────

class ParameterDetail(BaseModel):
    name:    Optional[str] = None
    type:    Optional[str] = None
    default: Optional[str] = None
    # positional_only | positional_or_keyword | positional | keyword_only | var_positional | var_keyword
    kind:    str = "positional"


class MethodDetail(BaseModel):
    name:           str
    signature:      str
    is_abstract:    bool = False
    is_constructor: bool = False
    visibility:     str  = "public"
    is_override:    bool = False

    # كلها اختيارية: التحليلات القديمة المحفوظة بـ Mongo ما فيها هالحقول.
    # body_hash = None معناها "الجسم غير معروف"، مش "الجسم فاضي".
    parameters:     Optional[List[ParameterDetail]] = None
    return_type:    Optional[str]       = None
    decorators:     List[str]           = Field(default_factory=list)
    docstring:      Optional[str]       = None
    is_async:       bool                = False
    body:           Optional[str]       = None
    body_hash:      Optional[str]       = None
    body_truncated: bool                = False
    line_start:     Optional[int]       = None
    line_end:       Optional[int]       = None


class AttributeDetail(BaseModel):
    name:       str
    type:       str = "any"
    visibility: str = "public"


class ClassDetail(BaseModel):
    name:          str
    type:          str
    methods:       List[MethodDetail]       = Field(default_factory=list)
    attributes:    List[AttributeDetail]    = Field(default_factory=list)
    relationships: List[Dict[str, Any]]     = Field(default_factory=list)
    is_generic:    bool = False
    is_abstract:   bool = False
    is_interface:  bool = False
    constraints:   List[str]                = Field(default_factory=list)


class UnifiedClassDiagram(BaseModel):
    classes:       List[ClassDetail]    = Field(default_factory=list)
    relationships: List[Dict[str, Any]] = Field(default_factory=list)
    language:      str = ""
    project_id:    Optional[str] = None


# ─────────────────────────────────────────────────────────────────────────────
# 5. ConflictItem
# ─────────────────────────────────────────────────────────────────────────────

class ConflictItem(BaseModel):
    conflict_id:        Optional[str]            = None
    type:               ChangeType
    severity:           SeverityLevel
    element:            Optional[Dict[str, Any]] = None
    class_name:         str
    member:             Optional[str]            = None
    line_number:        Optional[int]            = None
    description:        str
    old_value:          Optional[str]            = None
    new_value:          Optional[str]            = None
    old_logic:          Optional[str]            = None
    new_logic:          Optional[str]            = None
    code_value:         Optional[str]            = None
    doc_value:          Optional[str]            = None
    impact:             Optional[str]            = None
    suggestion:         Optional[str]            = None
    affected_files:     List[str]                = Field(default_factory=list)
    recommendation:     Optional[str]            = None
    auto_fix_available: bool  = False
    ai_confidence:      float = 0.0
    doc_type:           Optional[DocType] = None
    # اسم نمط التغيير (method_removed, class_added, ...). كان Optional[ChangeCategory]
    # بس structural_diff بيبعت أسماء أنماط مش syntactic/semantic/behavioral، فكان كل
    # تغيير هيكلي يوقّع المسار بـ ValidationError.
    category:           Optional[str] = None

    # ── Code vs Doc (DocPrism) ──
    doc_label:          Optional[DocConsistencyLabel] = None
    is_flagged:         Optional[bool] = None   # False = منحتفظ فيه بس ما منعرضه (متل Under_Promise)
    evidence:           Optional[str]  = None   # السطر من الكود + الجملة من التوثيق

    # ── Code vs Code ──
    decision:           Optional[ChangeDecision] = None
    risk_level:         Optional[RiskLevel] = None


# ─────────────────────────────────────────────────────────────────────────────
# 6. ConflictAnalysisResult
# ─────────────────────────────────────────────────────────────────────────────

class ConflictAnalysisResult(BaseModel):
    model_config = {"use_enum_values": True}

    analysis_id:   Optional[str] = None
    analysis_type: AnalysisType
    status:        str = "success"
    message:       str = ""
    completed_at:  Optional[datetime] = None
    execution_time_seconds: Optional[float] = None

    metadata: Optional[ConflictMetadata] = None

    version_a: str
    version_b: Optional[str] = None

    diagram_a: UnifiedClassDiagram
    diagram_b: Optional[UnifiedClassDiagram] = None

    structural_conflicts: List[ConflictItem] = Field(default_factory=list)
    semantic_conflicts:   List[ConflictItem] = Field(default_factory=list)
    doc_conflicts:        List[ConflictItem] = Field(default_factory=list)

    conflicts: Optional[Dict[str, List[ConflictItem]]] = None

    summary:                str   = ""
    breaking_changes_count: int   = 0
    compatibility_score:    Optional[float] = None

    total_changes:   int  = 0
    total_conflicts: int  = 0
    grade:           str  = "B"
    suggestions:     List[Dict[str, Any]] = Field(default_factory=list)
