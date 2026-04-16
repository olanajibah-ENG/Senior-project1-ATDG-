"""
Evaluation Service for AI Explanations
Implements 4-layer scoring system for explanation quality evaluation
"""

import re
import ast
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from bson import ObjectId
from core_ai.mongo_utils import get_mongo_db
from core_ai.ai_engine.llm_client import LLMClient

logger = logging.getLogger(__name__)


class ExplanationEvaluator:
    """Complete 4-layer evaluation system for AI explanations"""
    
    def __init__(self):
        self.db = get_mongo_db()
    
    def evaluate_explanation(self, explanation_id: str, force_reevaluate: bool = False) -> Dict[str, Any]:
        """Main evaluation method - runs all 4 layers"""
        
        # Load required data from MongoDB
        if self.db is None:
            raise Exception("Database connection failed")
        
        # Get explanation
        explanation_collection = self.db["ai_explanations"]
        explanation = explanation_collection.find_one({"_id": ObjectId(explanation_id)})
        
        if explanation is None:
            raise Exception(f"Explanation with ID {explanation_id} not found")
        
        # Get analysis
        analysis_collection = self.db["analysis_results"]
        analysis = analysis_collection.find_one({"_id": ObjectId(explanation["analysis_id"])})
        
        if analysis is None:
            raise Exception(f"Analysis with ID {explanation['analysis_id']} not found")
        
        # Check for existing evaluation
        if not force_reevaluate:
            existing_eval = self.db["explanation_evaluations"].find_one(
                {"explanation_id": explanation_id},
                sort=[("evaluated_at", -1)]
            )
            if existing_eval:
                return existing_eval
        
        # Get human feedback count
        human_feedback_count = self._get_human_feedback_count()
        
        # Run evaluation layers
        layer1_result = self._layer1_ast_cross_check(explanation, analysis)
        layer2_result = self._layer2_completeness_check(explanation, analysis)
        layer3_result = self._layer3_llm_judge(explanation, analysis)
        layer4_result = self._layer4_human_review(explanation)
        
        # Calculate final score
        final_score = self._calculate_final_score(
            layer1_result["score"],
            layer2_result["score"],
            layer3_result["score"],
            layer4_result["human_score"]
        )
        
        # Determine verdict
        verdict = self._get_verdict(final_score)
        
        # Build evaluation result
        evaluation_result = {
            "explanation_id": explanation_id,
            "layer3_method": "llm" if not layer3_result.get("llm_failed") else "rule_based",
            "human_reviewed": layer4_result["human_score"] is not None,
            "layer1": layer1_result,
            "layer2": layer2_result,
            "layer3": layer3_result,
            "layer4": layer4_result,
            "final_score": final_score,
            "final_score_percentage": final_score * 100,
            "overall_verdict": verdict,
            "evaluated_at": datetime.utcnow()
        }
        
        # Save to database
        self._save_evaluation(evaluation_result)
        
        return evaluation_result
    
    def _get_human_feedback_count(self) -> int:
        """Get total human feedback count from system"""
        # This would query a collection that tracks human reviews
        # For now, return 0 as placeholder
        feedback_collection = self.db["human_feedback"]
        return feedback_collection.count_documents({})
    
    def _name_mentioned(self, name: str, text: str) -> bool:
        """
        Check if a code element name is mentioned in explanation text.
        Uses 3 strategies in order:

        1. Exact match — "get_tasks" literally in text
        2. Backtick match — `get_tasks` or `get_tasks()` in text
        3. Part-based match — split name by underscore/camelCase,
           check if ALL meaningful parts (len > 2) appear in text
        """
        
        VERB_PREFIX_SYNONYMS = {
            "get":    ["retriev", "fetch", "list", "show", "return", "display"],
            "add":    ["creat", "insert", "new", "append", "post", "submit"],
            "create": ["creat", "insert", "new", "add", "post", "generat"],
            "update": ["updat", "modif", "edit", "chang", "patch", "put"],
            "delete": ["delet", "remov", "destroy", "drop"],
            "save":   ["sav", "persist", "store", "commit"],
            "load":   ["load", "read", "fetch", "retriev"],
            "send":   ["send", "emit", "dispatch", "publish", "notif"],
            "check":  ["check", "validat", "verify", "inspect"],
            "parse":  ["pars", "extract", "process", "analyz"],
            "build":  ["build", "construct", "generat", "creat"],
            "run":    ["run", "execut", "start", "launch", "trigger"],
            "init":   ["init", "setup", "configur", "boot", "start"],
            "to":     ["serial", "convert", "format", "transform"],
        }
        
        # Strategy 1: Exact match
        if name.lower() in text:
            return True
        
        # Strategy 2: Backtick match
        if f"`{name}`" in text or f"`{name}()`" in text:
            return True
        
        # Strategy 3: Part-based match (only for multi-word names)
        if '_' in name or any(c.isupper() for c in name[1:]):  # snake_case or camelCase
            # Split by underscore or camelCase
            if '_' in name:
                parts = name.split('_')
            else:
                # camelCase split
                parts = []
                current = ''
                for char in name:
                    if char.isupper():
                        if current:
                            parts.append(current.lower())
                        current = char.lower()
                    else:
                        current += char
                if current:
                    parts.append(current.lower())
            
            # Filter meaningful parts (len > 2)
            meaningful_parts = [p for p in parts if len(p) > 2]
            
            if len(meaningful_parts) >= 2:
                # Check for verb prefix synonyms
                verb_prefix = meaningful_parts[0]
                noun_parts = meaningful_parts[1:]
                
                synonym_match = False
                if verb_prefix in VERB_PREFIX_SYNONYMS:
                    for synonym in VERB_PREFIX_SYNONYMS[verb_prefix]:
                        if synonym in text:
                            synonym_match = True
                            break
                
                # Check noun parts
                noun_match = any(noun in text for noun in noun_parts if len(noun) > 3)
                
                # Both synonym and noun must match
                if synonym_match and noun_match:
                    return True
        
        return False
    
    def _layer1_ast_cross_check(self, explanation: dict, analysis: dict) -> Dict[str, Any]:
        """Layer 1: Faithfulness — هل الشرح ذكر عناصر الكود الحقيقية؟"""
        
        explanation_text = explanation.get("content", "")
        explanation_lower = explanation_text.lower()
        code_summary = self._build_code_summary_from_analysis(analysis)
        
        verified_claims = []
        hallucinated_claims = []
        
        # تحقق من كل class
        for cls in code_summary["classes"]:
            if self._name_mentioned(cls, explanation_lower):
                verified_claims.append({
                    "claim": f"Class {cls}",
                    "evidence": f"Class {cls} mentioned in explanation"
                })
            else:
                hallucinated_claims.append({
                    "claim": f"Class {cls} not mentioned",
                    "reason": f"Class {cls} exists in code but not mentioned in explanation"
                })
        
        # تحقق من كل function
        for func in code_summary["functions"]:
            if self._name_mentioned(func, explanation_lower):
                verified_claims.append({
                    "claim": f"Function {func}",
                    "evidence": f"Function {func} mentioned in explanation"
                })
            else:
                hallucinated_claims.append({
                    "claim": f"Function {func} not mentioned",
                    "reason": f"Function {func} exists in code but not mentioned in explanation"
                })
        
        # تحقق من كل dependency
        for dep in code_summary["dependencies"]:
            dep_mentioned = (dep.lower() in explanation_lower or 
                            dep.replace("_", " ").lower() in explanation_lower or
                            dep.replace("_", "-").lower() in explanation_lower)
            if dep_mentioned:
                verified_claims.append({
                    "claim": f"Dependency {dep}",
                    "evidence": f"Dependency {dep} mentioned in explanation"
                })
            else:
                hallucinated_claims.append({
                    "claim": f"Dependency {dep} not mentioned",
                    "reason": f"Dependency {dep} exists in code but not mentioned in explanation"
                })
        
        total = len(verified_claims) + len(hallucinated_claims)
        score = len(verified_claims) / total if total > 0 else 0.5
        
        return {
            "verified_claims": verified_claims,
            "hallucinated_claims": hallucinated_claims,
            "unverifiable_claims": [],
            "code_summary": code_summary,
            "score": score
        }
    def _extract_factual_claims(self, text: str) -> List[str]:
        """Extract factual claims from explanation text"""
        claims = []

        # Extract capitalized words near class-related keywords
        class_pattern = r'\b([A-Z][a-zA-Z0-9_]+)\b'
        cap_words = re.findall(class_pattern, text)
        claims.extend([f"Class {w}" for w in cap_words if len(w) > 1 and w not in {"The", "A", "An", "This", "GET", "POST", "PUT", "DELETE", "HTTP", "API", "Flask", "SQL", "SQLite", "SQLAlchemy"}])

        # Extract function/method names — words followed by ()
        method_pattern = r'`([a-z_][a-zA-Z0-9_]*)\(\)`'
        methods = re.findall(method_pattern, text)
        claims.extend([f"Method {m}" for m in methods])

        # Extract imports — look for backtick-quoted module names
        import_pattern = r'`([a-z_][a-zA-Z0-9_.]+)`'
        imports = re.findall(import_pattern, text)
        claims.extend([f"Import {i}" for i in imports if "." not in i])

        return list(set(claims))
    
    def _verify_claim(self, claim: str, analysis_data: Dict) -> bool:
        """Verify if claim exists in analysis data"""
        
        if not analysis_data:
            return False
        
        # Check against AST
        ast_data = analysis_data.get("ast", {})
        if "class_names" in ast_data and any(cls in claim for cls in ast_data["class_names"]):
            return True
        if "function_names" in ast_data and any(func in claim for func in ast_data["function_names"]):
            return True
        
        # Check against extracted features
        features = analysis_data.get("extracted_features", {})
        if "imports" in features and any(imp in claim for imp in features["imports"]):
            return True
        if "classes" in features and any(cls in claim for cls in features["classes"]):
            return True
        
        return False
    
    def _contradicts_claim(self, claim: str, analysis_data: Dict) -> bool:
        """Check if claim contradicts analysis data"""
        # For now, simplified - would need more sophisticated logic
        return False
    
    def _layer2_completeness_check(self, explanation: dict, analysis: dict) -> Dict[str, Any]:
        """Layer 2: Completeness Check"""
        
        explanation_text = explanation.get("content", "")
        
        # Build complete code inventory from analysis data instead of raw AST
        code_summary = self._build_code_summary_from_analysis(analysis)
        
        covered_elements = []
        missing_elements = []
        
        # Check coverage for classes
        for cls in code_summary["classes"]:
            if cls in explanation_text:
                covered_elements.append(f"Class: {cls}")
            else:
                missing_elements.append(f"Class: {cls}")
        
        # Check coverage for functions
        for func in code_summary["functions"]:
            if self._name_mentioned(func, explanation_text.lower()):
                covered_elements.append(f"Function: {func}")
            else:
                missing_elements.append(f"Function: {func}")
        
        # Check coverage for routes
        for route in code_summary["routes"]:
            if route["path"] in explanation_text or route["method"] in explanation_text:
                covered_elements.append(f"Route: {route['method']} {route['path']}")
            else:
                missing_elements.append(f"Route: {route['method']} {route['path']}")
        
        # Check coverage for dependencies
        for dep in code_summary["dependencies"]:
            if dep in explanation_text:
                covered_elements.append(f"Dependency: {dep}")
            else:
                missing_elements.append(f"Dependency: {dep}")
        
        # Calculate weighted coverage
        total_elements = {
            "classes": len(code_summary["classes"]),
            "functions": len(code_summary["functions"]),
            "routes": len(code_summary["routes"]),
            "dependencies": len(code_summary["dependencies"])
        }
        
        weights = {
            "classes": 0.30,
            "functions": 0.30,
            "dependencies": 0.20,
            "routes": 0.10,
            "complexity": 0.10
        }
        
        coverage_scores = {}
        for category, weight in weights.items():
            if category == "complexity":
                # Check if complexity is mentioned
                complexity_mentioned = any(word in explanation_text.lower() 
                                          for word in ["complex", "simple", "complicated", "straightforward"])
                coverage_scores[category] = 1.0 if complexity_mentioned else 0.5
            else:
                total = total_elements.get(category, 0)
                if total == 0:
                    coverage_scores[category] = 1.0
                else:
                    prefix_map = {"classes": "class:", "functions": "function:", "routes": "route:", "dependencies": "dependency:"}
                    prefix = prefix_map.get(category, category)
                    covered = len([e for e in covered_elements if e.lower().startswith(prefix)])
                    coverage_scores[category] = covered / total
        
        score = sum(coverage_scores[cat] * weights[cat] for cat in weights)
        
        return {
            "covered_elements": covered_elements,
            "missing_elements": missing_elements,
            "code_summary": code_summary,
            "coverage_scores": coverage_scores,
            "score": score
        }
    
    def _extract_inventory(self, analysis_data: Dict) -> Dict[str, List]:
        """Extract complete inventory from analysis data"""
        
        inventory = {
            "classes": [],
            "methods": [],
            "dependencies": [],
            "routes": [],
            "validation": []
        }
        
        ast_data = analysis_data.get("ast", {})
        features = analysis_data.get("extracted_features", {})
        
        # Extract classes
        inventory["classes"] = ast_data.get("class_names", [])
        
        # Extract methods/functions
        inventory["methods"] = ast_data.get("function_names", [])
        
        # Extract dependencies
        inventory["dependencies"] = features.get("imports", [])
        
        # Extract routes (if present)
        inventory["routes"] = features.get("routes", [])
        
        # Extract validation logic
        inventory["validation"] = features.get("validations", [])
        
        return inventory
    
    def _layer3_llm_judge(self, explanation: dict, analysis: dict) -> Dict[str, Any]:
        """Layer 3: LLM-as-a-Judge for linguistic quality"""
        
        text = explanation.get("content", "")
        
        # Build code summary for context from analysis data
        code_summary = self._build_code_summary_from_analysis(analysis)
        
        # Use real LLM for evaluation with code context
        llm_result = self._evaluate_with_llm(text, code_summary)
        
        return llm_result
    
    def _evaluate_clarity(self, text: str) -> float:
        """Evaluate clarity of explanation"""
        # Simple heuristic-based evaluation
        sentences = text.split('.')
        if not sentences:
            return 0.0
        
        # Check for clear structure
        has_intro = any(len(s.strip()) > 10 for s in sentences[:2])
        has_examples = "example" in text.lower() or "for instance" in text.lower()
        avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences)
        
        # Score based on clarity factors
        score = 0.0
        if has_intro:
            score += 0.3
        if has_examples:
            score += 0.2
        if 10 <= avg_sentence_length <= 25:
            score += 0.3
        else:
            score += 0.1
        
        return min(score, 1.0)
    
    def _evaluate_logical_flow(self, text: str) -> float:
        """Evaluate logical flow of explanation"""
        # Check for logical structure
        has_intro = any(word in text.lower()[:100] for word in ["this", "the", "here"])
        has_conclusion = any(word in text.lower()[-100:] for word in ["conclusion", "summary", "in summary"])
        
        # Check for transition words
        transitions = ["however", "therefore", "additionally", "furthermore", "moreover"]
        has_transitions = any(trans in text.lower() for trans in transitions)
        
        score = 0.0
        if has_intro:
            score += 0.3
        if has_conclusion:
            score += 0.3
        if has_transitions:
            score += 0.4
        
        return min(score, 1.0)
    
    def _evaluate_precision(self, text: str) -> float:
        """Evaluate precision (specificity to this code)"""
        # Check for code-specific terms
        code_terms = ["function", "class", "method", "variable", "parameter", "return"]
        has_code_terms = any(term in text.lower() for term in code_terms)
        
        # Check for generic vs specific language
        generic_phrases = ["this code", "the program", "the application"]
        has_generic = any(phrase in text.lower() for phrase in generic_phrases)
        
        score = 0.0
        if has_code_terms:
            score += 0.6
        if not has_generic:
            score += 0.4
        
        return min(score, 1.0)
    
    def _evaluate_no_redundancy(self, text: str) -> float:
        """Evaluate lack of redundancy"""
        sentences = [s.strip() for s in text.split('.') if s.strip()]
        if len(sentences) < 2:
            return 1.0
        
        # Check for repeated phrases
        phrases = []
        for sentence in sentences:
            words = sentence.lower().split()
            for i in range(len(words) - 2):
                phrase = ' '.join(words[i:i+3])
                phrases.append(phrase)
        
        # Count repetitions
        repetitions = sum(phrases.count(phrase) - 1 for phrase in set(phrases))
        
        # Score based on lack of repetition
        score = max(0.0, 1.0 - (repetitions / len(phrases)))
        
        return min(score, 1.0)
    
    def _generate_qualitative_summary(self, clarity: float, logical_flow: float, precision: float, no_redundancy: float) -> str:
        """Generate qualitative summary of evaluation"""
        strengths = []
        weaknesses = []
        
        if clarity >= 0.7:
            strengths.append("clear and easy to understand")
        if logical_flow >= 0.7:
            strengths.append("well-structured logical flow")
        if precision >= 0.7:
            strengths.append("specific to code")
        if no_redundancy >= 0.7:
            strengths.append("concise without repetition")
        
        if clarity < 0.5:
            weaknesses.append("unclear explanations")
        if logical_flow < 0.5:
            weaknesses.append("poor logical structure")
        if precision < 0.5:
            weaknesses.append("too generic")
        if no_redundancy < 0.5:
            weaknesses.append("repetitive content")
        
        summary = ""
        if strengths:
            summary += f"Strengths: {', '.join(strengths)}. "
        if weaknesses:
            summary += f"Weaknesses: {', '.join(weaknesses)}."
        
        return summary.strip()
    
    def _layer4_human_review(self, explanation: dict) -> Dict[str, Any]:
        """Layer 4: Human Reviewer Score"""
        
        # Check if human score exists for this explanation
        human_feedback_collection = self.db["human_feedback"]
        human_feedback = human_feedback_collection.find_one({"explanation_id": str(explanation.get("_id", ""))})
        
        if human_feedback and "score" in human_feedback:
            return {
                "human_score": human_feedback["score"],
                "human_comment": human_feedback.get("comment", None)
            }
        
        return {
            "human_score": None,
            "human_comment": None
        }
    
    def _calculate_final_score(self, layer1: float, layer2: float, layer3: float, layer4: Optional[float]) -> float:
        """4-layer weighted score. With human: 40/20/20/20. Without: 50/25/25"""
        if layer4 is not None:
            return (layer1 * 0.40) + (layer2 * 0.20) + (layer3 * 0.20) + (layer4 * 0.20)
        else:
            return (layer1 * 0.50) + (layer2 * 0.25) + (layer3 * 0.25)
    
    def _get_verdict(self, final_score: float) -> str:
        """Get overall verdict based on final score"""
        if final_score >= 0.85:
            return "EXCELLENT"
        elif final_score >= 0.70:
            return "GOOD"
        elif final_score >= 0.55:
            return "ACCEPTABLE"
        else:
            return "POOR"
    
    def _save_evaluation(self, evaluation_result: Dict[str, Any]) -> str:
        """Save evaluation result to MongoDB"""
        
        collection = self.db["explanation_evaluations"]
        
        # Insert evaluation result
        result = collection.insert_one(evaluation_result)
        
        return str(result.inserted_id)
    
    def _build_code_summary_from_analysis(self, analysis: dict) -> dict:
        """Build code summary from saved analysis results instead of raw AST"""
        
        features = analysis.get("extracted_features", {})
        class_data = analysis.get("class_diagram_data", {})
        
        routes = []
        for r in features.get("routes", []):
            for method in r.get("methods", ["GET"]):
                routes.append({
                    "path": r.get("path", ""),
                    "method": method
                })
        
        return {
            "classes": [c["name"] for c in class_data.get("classes", [])],
            "functions": features.get("function_names", []),
            "routes": routes,
            "dependencies": analysis.get("dependencies", []),
            "lines_of_code": features.get("lines_of_code", 0),
            "complexity": features.get("complexity_score", 0)
        }
    
    def _build_code_summary(self, ast_tree: Dict) -> Dict[str, Any]:
        """Build complete code summary from AST tree"""
        
        summary = {
            "classes": [],
            "functions": [],
            "routes": [],
            "dependencies": [],
            "lines_of_code": 0,
            "complexity": 0
        }
        
        if not ast_tree:
            return summary
        
        # Extract classes
        self._extract_classes_from_ast(ast_tree, summary)
        
        # Extract functions
        self._extract_functions_from_ast(ast_tree, summary)
        
        # Extract routes (Django decorators)
        self._extract_routes_from_ast(ast_tree, summary)
        
        # Extract dependencies
        self._extract_dependencies_from_ast(ast_tree, summary)
        
        # Calculate complexity
        summary["complexity"] = self._calculate_complexity(summary)
        
        return summary
    
    def _extract_classes_from_ast(self, node: Dict, summary: Dict):
        """Recursively extract class names from AST"""
        if isinstance(node, dict):
            if node.get("node_type") == "ClassDef":
                summary["classes"].append(node.get("name", ""))
            
            # Recursively check children
            for key, value in node.items():
                if isinstance(value, (dict, list)):
                    self._extract_classes_from_ast(value, summary)
        elif isinstance(node, list):
            for item in node:
                self._extract_classes_from_ast(item, summary)
    
    def _extract_functions_from_ast(self, node: Dict, summary: Dict):
        """Recursively extract function names from AST"""
        if isinstance(node, dict):
            if node.get("node_type") in ["FunctionDef", "AsyncFunctionDef"]:
                summary["functions"].append(node.get("name", ""))
            
            # Recursively check children
            for key, value in node.items():
                if isinstance(value, (dict, list)):
                    self._extract_functions_from_ast(value, summary)
        elif isinstance(node, list):
            for item in node:
                self._extract_functions_from_ast(item, summary)
    
    def _extract_routes_from_ast(self, node: Dict, summary: Dict):
        """Extract route decorators from AST"""
        if isinstance(node, dict):
            # Check for Flask route decorators
            decorators = node.get("decorator_list", [])
            if isinstance(decorators, list):
                for decorator in decorators:
                    if isinstance(decorator, dict):
                        func = decorator.get("func", {})
                        
                        # Handle Flask @app.route with Attribute node_type
                        if func.get("node_type") == "Attribute" and func.get("attr") == "route":
                            # Extract route path
                            args = decorator.get("args", [])
                            if args and isinstance(args[0], dict):
                                path = args[0].get("value", "").strip('\"\'')
                                
                                # Extract methods from keywords
                                keywords = decorator.get("keywords", [])
                                methods = ["GET"]  # default
                                
                                for kw in keywords:
                                    if kw.get("arg", "") == "methods":
                                        methods_list = kw.get("value", {})
                                        if isinstance(methods_list, dict) and "elts" in methods_list:
                                            # Extract method strings from elts
                                            method_nodes = methods_list["elts"]
                                            if isinstance(method_nodes, list):
                                                methods = []
                                                for method_node in method_nodes:
                                                    if isinstance(method_node, dict):
                                                        method_value = method_node.get("value", "")
                                                        if method_value:
                                                            methods.append(str(method_value))
                                
                                # Add each method as separate route entry
                                for method in methods:
                                    summary["routes"].append({
                                        "path": path,
                                        "method": method
                                    })
                        
                        # Handle simple function decorators
                        elif isinstance(func, str):
                            func_id = func
                            
                            # Handle DRF @api_view
                            if func_id == "api_view":
                                summary["routes"].append({
                                    "path": "DRF View",
                                    "method": "API"
                                })
                            
                            # Handle HTTP method decorators
                            elif func_id in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
                                args = decorator.get("args", [])
                                if args and isinstance(args[0], dict):
                                    path = args[0].get("value", "").strip('\"\'')
                                    summary["routes"].append({
                                        "path": path,
                                        "method": func_id
                                    })
                        
                        # Handle direct function calls
                        elif func.get("id", "") in ["route", "api_view", "GET", "POST", "PUT", "DELETE", "PATCH"]:
                            func_id = func.get("id", "")
                            
                            if func_id == "route":
                                args = decorator.get("args", [])
                                if args and isinstance(args[0], dict):
                                    path = args[0].get("value", "").strip('\"\'')
                                    keywords = decorator.get("keywords", [])
                                    methods = ["GET"]
                                    
                                    for kw in keywords:
                                        if kw.get("arg", "") == "methods":
                                            methods_list = kw.get("value", {})
                                            if isinstance(methods_list, dict) and "elts" in methods_list:
                                                method_nodes = methods_list["elts"]
                                                if isinstance(method_nodes, list):
                                                    methods = []
                                                    for method_node in method_nodes:
                                                        if isinstance(method_node, dict):
                                                            method_value = method_node.get("value", "")
                                                            if method_value:
                                                                methods.append(str(method_value))
                                    
                                    # Add each method as separate route entry
                                    for method in methods:
                                        summary["routes"].append({
                                            "path": path,
                                            "method": method
                                        })
                            elif func_id == "api_view":
                                summary["routes"].append({
                                    "path": "DRF View",
                                    "method": "API"
                                })
                            elif func_id in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
                                args = decorator.get("args", [])
                                if args and isinstance(args[0], dict):
                                    path = args[0].get("value", "").strip('\"\'')
                                    summary["routes"].append({
                                        "path": path,
                                        "method": func_id
                                    })
            
            # Recursively check children
            for key, value in node.items():
                if isinstance(value, (dict, list)):
                    self._extract_routes_from_ast(value, summary)
        elif isinstance(node, list):
            for item in node:
                self._extract_routes_from_ast(item, summary)
    
    def _extract_dependencies_from_ast(self, node: Dict, summary: Dict):
        """Extract import statements from AST"""
        if isinstance(node, dict):
            if node.get("node_type") == "Import":
                names = node.get("names", [])
                if isinstance(names, list):
                    for name in names:
                        if isinstance(name, dict):
                            summary["dependencies"].append(name.get("name", ""))
            elif node.get("node_type") == "ImportFrom":
                module = node.get("module", "")
                if module:
                    summary["dependencies"].append(module)
            
            # Recursively check children
            for key, value in node.items():
                if isinstance(value, (dict, list)):
                    self._extract_dependencies_from_ast(value, summary)
        elif isinstance(node, list):
            for item in node:
                self._extract_dependencies_from_ast(item, summary)
    
    def _calculate_complexity(self, summary: Dict) -> int:
        """Calculate cyclomatic complexity"""
        complexity = 1  # Base complexity
        
        # Add complexity for each function
        complexity += len(summary["functions"])
        
        # Add complexity for each class
        complexity += len(summary["classes"]) * 2
        
        # Add complexity for routes
        complexity += len(summary["routes"])
        
        return complexity
    
    def _verify_claim_against_code(self, claim: str, code_summary: Dict) -> Dict[str, Any]:
        """Verify a claim against actual code summary"""
        
        claim_lower = claim.lower()
        
        # Check class claims
        if "class" in claim_lower:
            for cls in code_summary["classes"]:
                if cls.lower() in claim_lower:
                    return {
                        "verified": True,
                        "contradicted": False,
                        "evidence": f"Class {cls} found in code"
                    }
            return {
                "verified": False,
                "contradicted": True,
                "reason": "No matching class found in code"
            }
        
        # Check function claims
        if "function" in claim_lower or "method" in claim_lower:
            for func in code_summary["functions"]:
                if func.lower() in claim_lower:
                    return {
                        "verified": True,
                        "contradicted": False,
                        "evidence": f"Function {func} found in code"
                    }
            return {
                "verified": False,
                "contradicted": True,
                "reason": "No matching function found in code"
            }
        
        # Check dependency claims
        if "import" in claim_lower:
            for dep in code_summary["dependencies"]:
                if dep.lower() in claim_lower:
                    return {
                        "verified": True,
                        "contradicted": False,
                        "evidence": f"Import {dep} found in code"
                    }
            return {
                "verified": False,
                "contradicted": True,
                "reason": "No matching import found in code"
            }
        
        # Cannot verify other types of claims
        return {
            "verified": False,
            "contradicted": False,
            "reason": "Claim type cannot be verified from AST"
        }
    
    def _evaluate_with_llm(self, text: str, code_summary: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate using LLM — tries each model once, fast fallback if all fail"""
        import requests
        from django.conf import settings

        models_to_try = [
            "qwen/qwen3-coder:free",
            "nvidia/nemotron-3-nano-30b-a3b:free",
            "meta-llama/llama-3.2-3b-instruct:free",
        ]

        functions_list = code_summary.get('functions', [])[:4]
        deps_list = code_summary.get('dependencies', [])[:3]
        text_short = text[:600] if len(text) > 600 else text

        prompt = f"""Rate this code explanation (0.0-1.0 each).
Code: classes={code_summary.get('classes', [])}, functions={functions_list}, deps={deps_list}
Explanation: {text_short}
Return ONLY JSON: {{"clarity":<float>,"logical_flow":<float>,"precision":<float>,"no_redundancy":<float>,"score":<avg>,"qualitative_summary":"<1 sentence>"}}"""

        api_key = getattr(settings, "OPENROUTER_API_KEY", None)
        if not api_key:
            logger.warning("[EVAL] No API key — using heuristic fallback")
            result = self._fallback_heuristic_evaluation(text)
            result["llm_failed"] = True
            return result

        for model in models_to_try:
            try:
                response = requests.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": model,
                        "messages": [
                            {"role": "system", "content": "You are a code explanation evaluator. Return only valid JSON."},
                            {"role": "user", "content": prompt}
                        ],
                        "max_tokens": 200,
                        "temperature": 0.1
                    },
                    timeout=15
                )

                if response.status_code == 429:
                    logger.warning(f"[EVAL] Rate limit on {model} — trying next")
                    continue

                if response.status_code != 200:
                    logger.warning(f"[EVAL] {model} returned {response.status_code} — trying next")
                    continue

                content_text = response.json()['choices'][0]['message']['content']
                json_start = content_text.find("{")
                json_end = content_text.rfind("}") + 1
                if json_start != -1 and json_end > json_start:
                    parsed = json.loads(content_text[json_start:json_end])
                    if all(k in parsed for k in ["clarity", "logical_flow", "precision", "no_redundancy", "score", "qualitative_summary"]):
                        logger.info(f"[EVAL] LLM success with {model}")
                        return parsed

            except Exception as e:
                logger.warning(f"[EVAL] {model} error: {str(e)[:60]} — trying next")
                continue

        logger.warning("[EVAL] All models failed — heuristic fallback")
        result = self._fallback_heuristic_evaluation(text)
        result["llm_failed"] = True
        return result
    def _fallback_heuristic_evaluation(self, text: str) -> Dict[str, Any]:
        """Fallback heuristic evaluation if LLM fails"""
        
        clarity = self._evaluate_clarity(text)
        logical_flow = self._evaluate_logical_flow(text)
        precision = self._evaluate_precision(text)
        no_redundancy = self._evaluate_no_redundancy(text)
        
        score = (clarity + logical_flow + precision + no_redundancy) / 4
        summary = self._generate_qualitative_summary(clarity, logical_flow, precision, no_redundancy)
        
        return {
            "clarity": clarity,
            "logical_flow": logical_flow,
            "precision": precision,
            "no_redundancy": no_redundancy,
            "score": score,
            "qualitative_summary": summary
        }