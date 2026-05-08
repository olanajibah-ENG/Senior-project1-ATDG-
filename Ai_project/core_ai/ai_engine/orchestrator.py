"""
orchestrator.py — Documentation Orchestrator
Implements LangGraph-style conditional routing without requiring langgraph
as a dependency. Uses a simple StateGraph-compatible runner.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

from bson import ObjectId
from django.conf import settings

from ..mongo_utils import get_mongo_db
from .agents import (
    DocumentationState,
    HighLevelAgent,
    LowLevelAgent,
    ProjectHighLevelAgent,
    ProjectLowLevelAgent,
    VerifierAgent,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Routing helpers
# ---------------------------------------------------------------------------

def _route_generation(state: DocumentationState) -> str:
    if state.is_project:
        return "project_high_level" if state.exp_type == "high_level" else "project_low_level"
    return "high_level" if state.exp_type == "high_level" else "low_level"


def _should_verify(state: DocumentationState) -> str:
    if state.error or not state.raw_output:
        return "done"
    return "verify"


# ---------------------------------------------------------------------------
# Lightweight graph runner (mirrors LangGraph StateGraph.compile().invoke())
# ---------------------------------------------------------------------------

class _SimpleGraph:
    """
    Minimal StateGraph-compatible runner.
    Replaces langgraph.StateGraph without the dependency.
    """

    def __init__(self):
        self._hl  = HighLevelAgent()
        self._ll  = LowLevelAgent()
        self._phl = ProjectHighLevelAgent()
        self._pll = ProjectLowLevelAgent()
        self._ver = VerifierAgent()

    def invoke(self, state: DocumentationState) -> DocumentationState:
        # Step 1: route to generation node
        route = _route_generation(state)
        node_map = {
            "high_level":         self._hl.as_node,
            "low_level":          self._ll.as_node,
            "project_high_level": self._phl.as_node,
            "project_low_level":  self._pll.as_node,
        }
        state = node_map[route](state)

        # Step 2: optional verification (Self-Refine step)
        if _should_verify(state) == "verify":
            state = self._ver.as_node(state)

        return state


_GRAPH = _SimpleGraph()


# ---------------------------------------------------------------------------
# DocumentationOrchestrator
# ---------------------------------------------------------------------------

class DocumentationOrchestrator:
    """
    Orchestrates explanation generation for a single analysis record.
    Public interface unchanged: get_or_generate_explanation(exp_type) → (content, id)
    """

    def __init__(self, analysis_id: str):
        self.analysis_id = analysis_id
        self.db = get_mongo_db()
        self.collection = self.db[
            getattr(settings, "AI_EXPLANATIONS_COLLECTION", "ai_explanations")
        ]
        self._is_object_id = ObjectId.is_valid(analysis_id)
        self._query_id = ObjectId(analysis_id) if self._is_object_id else str(analysis_id)

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def get_or_generate_explanation(self, exp_type: str) -> tuple:
        normalized = self._normalize_exp_type(exp_type)
        logger.info(f"[Orchestrator] exp_type='{exp_type}' → normalized='{normalized}'")

        # 1. Return cached explanation if it exists
        existing = self._find_existing(normalized)
        if existing:
            logger.info(f"[Orchestrator] Returning cached {normalized} explanation")
            return existing["content"], str(existing["_id"])

        # 2. Load analysis data
        analysis_data, is_project = self._load_analysis()
        if not analysis_data:
            raise Exception("Analysis record not found.")

        # Resolve UUID → ObjectId after loading
        if not self._is_object_id and analysis_data:
            self._query_id = analysis_data["_id"]

        # 3. Build LangGraph state
        state = self._build_state(analysis_data, is_project, normalized)

        # 4. Run the graph
        logger.info(f"[Orchestrator] Running graph for {normalized} (project={is_project})")
        final_state = _GRAPH.invoke(state)

        if final_state.error:
            raise Exception(
                f"Failed to generate {normalized} explanation: {final_state.error}"
            )

        content = final_state.verified_output or final_state.raw_output
        if not content:
            raise Exception(f"Graph produced no output for {normalized}")

        # 5. Persist
        doc_id = self._save(content, normalized, exp_type, is_project, state.code_content)
        return content, doc_id

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize_exp_type(exp_type: str) -> str:
        et = (str(exp_type) or "").strip().lower()
        high_variants = {"high", "high_level", "high-level", "executive", "business"}
        low_variants  = {"low",  "low_level",  "low-level",  "technical", "detailed"}
        words = set(et.replace("-", "_").split("_"))
        if words & high_variants:
            return "high_level"
        if words & low_variants:
            return "low_level"
        return "high_level"  # safe default

    def _find_existing(self, normalized: str):
        queries = [
            {"analysis_id": self._query_id, "exp_type": normalized},
            {"analysis_id": self._query_id, "explanation_type": normalized},
        ]
        if not self._is_object_id:
            queries += [
                {"analysis_id": str(self.analysis_id), "exp_type": normalized},
                {"analysis_id": str(self.analysis_id), "explanation_type": normalized},
            ]
        for q in queries:
            doc = self.collection.find_one(q)
            if doc:
                return doc
        return None

    def _load_analysis(self):
        if self._is_object_id:
            oid = ObjectId(self.analysis_id)
            doc = self.db[settings.ANALYSIS_RESULTS_COLLECTION].find_one({"_id": oid})
            if doc:
                return doc, False
            doc = self.db["project_analysis_results"].find_one({"_id": oid})
            if doc:
                return doc, True
        else:
            doc = self.db["project_analysis_results"].find_one(
                {"project_id": str(self.analysis_id)}
            )
            if doc:
                return doc, True
        return None, False

    def _build_state(
        self, analysis_data: dict, is_project: bool, normalized: str
    ) -> DocumentationState:
        semantic_data      = analysis_data.get("semantic_analysis_data") or {}
        class_diagram_data = analysis_data.get("class_diagram_data") or {}
        extracted_features = analysis_data.get("extracted_features") or {}

        if is_project:
            contexts      = analysis_data.get("contexts") or {}
            ordered_files = analysis_data.get("dependency_order") or []
            code_content  = (
                "PROJECT ARCHITECTURE OVERVIEW\n\n"
                f"Total Files: {len(ordered_files)}\n"
                f"Execution Order: {' -> '.join(ordered_files)}\n\n"
            )
            for f_context in contexts.values():
                code_content += f"{f_context}\n\n"
            code_content += "\n=== PROJECT CODE CONTENT ===\n"
            ast_struct = analysis_data.get("ast_structure") or {}
            code_content += ast_struct.get("code_content", "")
        else:
            ast_struct   = analysis_data.get("ast_structure") or {}
            code_content = ast_struct.get("code_content", "")

        # Resolve file name for single-file explanations
        file_name = None
        if not is_project:
            code_file_id = analysis_data.get("code_file_id")
            if code_file_id:
                coll = self.db[getattr(settings, "CODE_FILES_COLLECTION", "code_files")]
                qid  = ObjectId(code_file_id) if ObjectId.is_valid(str(code_file_id)) else code_file_id
                fdoc = coll.find_one({"_id": qid})
                if fdoc:
                    file_name = fdoc.get("filename")

        # Class name (first class found)
        classes    = class_diagram_data.get("classes") or []
        class_name = classes[0].get("name") if classes else None

        # Build summaries — both are always computed; agents pick what they need
        analysis_summary  = self._prepare_high_level_summary(
            semantic_data, class_diagram_data, extracted_features
        )
        detailed_analysis = self._prepare_low_level_analysis(
            semantic_data, class_diagram_data, extracted_features
        )

        return DocumentationState(
            code_content=code_content or "",
            detailed_analysis=detailed_analysis,
            analysis_summary=analysis_summary,
            class_name=class_name,
            file_name=file_name,
            exp_type=normalized,
            is_project=is_project,
        )

    def _save(
        self,
        content: str,
        normalized: str,
        original_exp_type: str,
        is_project: bool,
        code_content: str,
    ) -> str:
        agent_type_map = {
            ("high_level", False): "HighLevelAgent",
            ("high_level", True):  "ProjectHighLevelAgent",
            ("low_level",  False): "LowLevelAgent",
            ("low_level",  True):  "ProjectLowLevelAgent",
        }
        doc = {
            "analysis_id":           self._query_id,
            "exp_type":              normalized,
            "explanation_type":      normalized,
            "content":               content,
            "created_at":            datetime.utcnow(),
            "code_content":          code_content,
            "agent_type":            agent_type_map.get((normalized, is_project), "Unknown"),
            "original_request_type": str(original_exp_type),
            "normalized_type":       normalized,
            "is_project":            is_project,
        }
        result = self.collection.insert_one(doc)
        logger.info(f"[Orchestrator] Saved {normalized} explanation → {result.inserted_id}")
        return str(result.inserted_id)

    # ------------------------------------------------------------------
    # Analysis preparation helpers
    # ------------------------------------------------------------------

    def _prepare_high_level_summary(
        self, semantic_data: dict, class_diagram_data: dict, extracted_features: dict
    ) -> Optional[str]:
        parts = []
        classes = semantic_data.get("classes") or class_diagram_data.get("classes") or []

        if classes:
            names = [c.get("name", "Unknown") for c in classes if isinstance(c, dict)]
            if names:
                parts.append(f"Classes found: {', '.join(names)}")

            all_methods = []
            for cls in classes:
                if not isinstance(cls, dict):
                    continue
                for m in cls.get("methods", []):
                    if isinstance(m, str):
                        all_methods.append(m)
                    elif isinstance(m, dict):
                        all_methods.append(m.get("name", ""))
            if all_methods:
                parts.append(f"Main methods/functions: {', '.join(set(all_methods[:10]))}")

        if extracted_features:
            loc   = extracted_features.get("lines_of_code", 0)
            funcs = extracted_features.get("functions") or extracted_features.get("methods", 0)
            if loc or funcs:
                parts.append(f"Code statistics: {loc} lines, {funcs} functions/methods")

        return "\n".join(parts) if parts else None

    def _prepare_low_level_analysis(
        self, semantic_data: dict, class_diagram_data: dict, extracted_features: dict
    ) -> Optional[str]:
        parts = []
        classes = (
            semantic_data.get("classes") or class_diagram_data.get("classes") or []
        )

        patterns = self._detect_design_patterns(classes)
        if patterns:
            parts.append("=== DETECTED DESIGN PATTERNS ===")
            parts.extend(f"- {p}" for p in patterns)

        if classes:
            parts.append("=== CLASSES AND RELATIONSHIPS ===")
            inheritance_map = {}
            composition_map = {}

            for cls in classes:
                if not isinstance(cls, dict):
                    continue
                name    = cls.get("name", "Unknown")
                parents = cls.get("inherits") or cls.get("inheritance") or []
                if parents:
                    inheritance_map[name] = parents
                assocs = cls.get("associations") or cls.get("relationships") or []
                if assocs:
                    composition_map[name] = assocs

            if inheritance_map or composition_map:
                parts.append("\n** RELATIONSHIP ANALYSIS **")
                for child, parents in inheritance_map.items():
                    p_str = ", ".join(parents) if isinstance(parents, list) else str(parents)
                    parts.append(f"  - {child} inherits from: {p_str}")
                for cname, assocs in composition_map.items():
                    for a in assocs:
                        if isinstance(a, dict):
                            target   = a.get("target_class", a.get("target", "Unknown"))
                            rel_type = a.get("type", "association")
                            parts.append(f"  - {cname} --{rel_type}--> {target}")

            parts.append("\n** DETAILED CLASS ANALYSIS **")
            for cls in classes:
                if not isinstance(cls, dict):
                    continue
                name    = cls.get("name", "Unknown")
                methods = cls.get("methods") or []
                attrs   = cls.get("attributes") or cls.get("properties") or []

                header = f"\nClass: {name}"
                if name in inheritance_map:
                    header += f" (extends: {', '.join(inheritance_map[name])})"
                parts.append(header)

                if attrs:
                    parts.append("  Attributes/Properties:")
                    for attr in attrs:
                        if isinstance(attr, dict):
                            parts.append(
                                f"    - {attr.get('visibility', 'public')} "
                                f"{attr.get('name', '')}: {attr.get('type', 'Any')}"
                            )
                        else:
                            parts.append(f"    - {attr}")

                if methods:
                    parts.append("  Methods:")
                    for m in methods:
                        if isinstance(m, dict):
                            params = [
                                f"{p.get('name')}: {p.get('type', 'Any')}"
                                if isinstance(p, dict) else str(p)
                                for p in m.get("parameters", [])
                            ]
                            parts.append(
                                f"    - {m.get('visibility', 'public')} "
                                f"{m.get('name', '')}({', '.join(params)}) "
                                f"-> {m.get('return_type', 'void')}"
                            )
                        else:
                            parts.append(f"    - {m}()")

        if extracted_features:
            parts.append("\n=== CODE COMPLEXITY & STATS ===")
            for label, key in [
                ("Lines of Code",    "lines_of_code"),
                ("Total Methods",    "functions"),
                ("Complexity Index", "complexity"),
            ]:
                val = extracted_features.get(key)
                if isinstance(val, dict):
                    val = val.get("cyclomatic_complexity")
                if val:
                    parts.append(f"{label}: {val}")

        return "\n".join(parts) if parts else None

    def _detect_design_patterns(self, classes: list) -> list:
        patterns = []
        if not classes:
            return patterns

        class_names          = []
        factory_indicators   = []
        singleton_indicators = []
        inheritance_count    = 0

        for cls in classes:
            if not isinstance(cls, dict):
                continue
            name = cls.get("name", "")
            class_names.append(name.lower())

            if any(kw in name.lower() for kw in ("factory", "builder", "creator")):
                factory_indicators.append(name)

            method_names = []
            for m in cls.get("methods", []):
                if isinstance(m, str):
                    method_names.append(m.lower())
                elif isinstance(m, dict) and m.get("name"):
                    method_names.append(m["name"].lower())

            if "getinstance" in method_names or "instance" in method_names:
                singleton_indicators.append(name)

            if cls.get("inherits") or cls.get("inheritance") or cls.get("bases"):
                inheritance_count += 1

        if factory_indicators:
            patterns.append(f"Factory Pattern detected in: {', '.join(factory_indicators)}")
        if singleton_indicators:
            patterns.append(f"Singleton Pattern detected in: {', '.join(singleton_indicators)}")
        if inheritance_count > 1:
            patterns.append(
                f"Inheritance hierarchy detected ({inheritance_count} classes with inheritance)"
            )
        for keyword, label in (
            ("adapter",  "Adapter Pattern detected"),
            ("observer", "Observer Pattern detected"),
            ("strategy", "Strategy Pattern detected"),
        ):
            if any(keyword in n for n in class_names):
                patterns.append(label)

        return patterns
