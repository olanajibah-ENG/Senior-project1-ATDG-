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

class MethodDetail(BaseModel):
    name:           str
    signature:      str
    is_abstract:    bool = False
    is_constructor: bool = False
    visibility:     str  = "public"
    is_override:    bool = False


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
    category:           Optional[str]            = None
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
