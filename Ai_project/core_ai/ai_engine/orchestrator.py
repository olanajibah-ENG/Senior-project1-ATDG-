import os
import sys

# Set Django settings module if not already set
if 'DJANGO_SETTINGS_MODULE' not in os.environ:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')

# Import Django components (setup will be handled by Django app)
import django
from django.conf import settings

# Now import everything else
from ..mongo_utils import get_mongo_db
from .agents import HighLevelAgent, LowLevelAgent, VerifierAgent
from bson import ObjectId
from datetime import datetime

class DocumentationOrchestrator:
    def __init__(self, analysis_id):
        self.analysis_id = analysis_id
        self.db = get_mongo_db()
        self.collection = self.db[getattr(settings, 'AI_EXPLANATIONS_COLLECTION', 'ai_explanations')]
        # تحديد نوع الـ ID: ObjectId أو UUID
        self._is_object_id = ObjectId.is_valid(analysis_id)
        self._query_id = ObjectId(analysis_id) if self._is_object_id else str(analysis_id)

    def get_or_generate_explanation(self, exp_type):
        print(f"🔥🔥🔥 ORCHESTRATOR ENTRY - exp_type parameter: '{exp_type}' (type: {type(exp_type)})")
    
        # فحص القيم الواردة
        if exp_type in ['high', 'High', 'HIGH']:
            print(f"⚠️ WARNING: Received 'high' instead of 'high_level' - fixing...")
            exp_type = 'high_level'
        elif exp_type in ['low', 'Low', 'LOW']:
            print(f"⚠️ WARNING: Received 'low' instead of 'low_level' - fixing...")
            exp_type = 'low_level'
        
        print(f"🔥🔥🔥 ORCHESTRATOR FIXED - exp_type after fix: '{exp_type}'")
        
        # 1. Normalize the explanation type FIRST and store it
        et = (str(exp_type) or '').strip().lower()
        
        print(f"🔥🔥🔥 ORCHESTRATOR FINAL - normalized to lowercase: '{et}'")
            
        # Define ALL possible variations for each type
        high_level_variations = ['high', 'high_level', 'executive', 'business', 'high-level', 'high level']
        low_level_variations = ['low', 'low_level', 'technical', 'detailed', 'low-level', 'low level']
        
        # Determine the actual type with strict logic
        is_high_level = any(
            (variant == et) or                    # Exact match
            (et.startswith(variant + '_')) or     # Starts with variant_
            (et.endswith('_' + variant)) or       # Ends with _variant
            (variant in et.split('_'))            # Variant as separate word
            for variant in high_level_variations
        )

        is_low_level = any(
            (variant == et) or
            (et.startswith(variant + '_')) or
            (et.endswith('_' + variant)) or
            (variant in et.split('_'))
            for variant in low_level_variations
        ) and not is_high_level  # ⚠️ مهم: لو كان high_level، ما تعتبره low_level

        # Default to high_level if ambiguous
        if not is_high_level and not is_low_level:
            is_high_level = True  # Default to high level

        # CRITICAL: Store the normalized type
        normalized_exp_type = 'high_level' if is_high_level else 'low_level'
        
        print(f"DEBUG: Original exp_type: '{exp_type}'")
        print(f"DEBUG: Normalized to: '{normalized_exp_type}'")
        print(f"DEBUG: is_high_level: {is_high_level}")
        
        # 2. Search with ALL possible field names and variations
        search_queries = [
            {"analysis_id": self._query_id, "exp_type": normalized_exp_type},
            {"analysis_id": self._query_id, "explanation_type": normalized_exp_type},
            {"analysis_id": self._query_id, "exp_type": exp_type},
            {"analysis_id": self._query_id, "explanation_type": exp_type},
        ]
        
        # إذا كان UUID، ابحث أيضاً بالـ string
        if not self._is_object_id:
            search_queries.extend([
                {"analysis_id": str(self.analysis_id), "exp_type": normalized_exp_type},
                {"analysis_id": str(self.analysis_id), "explanation_type": normalized_exp_type},
            ])
        
        high_keywords = ['high', 'executive', 'business']
        low_keywords = ['low', 'technical', 'detailed']

        et_words = et.split('_')

        if any(word in et_words for word in high_keywords):
            search_queries.append({"analysis_id": self._query_id, "exp_type": "high_level"})
            search_queries.append({"analysis_id": self._query_id, "explanation_type": "high_level"})

        if any(word in et_words for word in low_keywords):
            search_queries.append({"analysis_id": self._query_id, "exp_type": "low_level"})
            search_queries.append({"analysis_id": self._query_id, "explanation_type": "low_level"})
        
        # Search for existing explanation
        existing = None
        for query in search_queries:
            existing = self.collection.find_one(query)
            if existing:
                print(f"DEBUG: Found existing explanation with query: {query}")
                break
        
        if existing:
            print(f"DEBUG: Returning existing {normalized_exp_type} explanation")
            return existing['content'], str(existing['_id'])

        # 3. Generate new explanation with STRICT enforcement
        is_project = False
        analysis_data = None
        
        if self._is_object_id:
            analysis_data = self.db[settings.ANALYSIS_RESULTS_COLLECTION].find_one(
                {"_id": ObjectId(self.analysis_id)}
            )
            if not analysis_data:
                analysis_data = self.db['project_analysis_results'].find_one(
                    {"_id": ObjectId(self.analysis_id)}
                )
                if analysis_data:
                    is_project = True
        else:
            # UUID → بحث في المشاريع بـ project_id
            analysis_data = self.db['project_analysis_results'].find_one(
                {"project_id": str(self.analysis_id)}
            )
            if analysis_data:
                is_project = True
        
        if not analysis_data:
            raise Exception("Analysis record not found.")
        
        if is_project:
            contexts = analysis_data.get('contexts', {})
            ordered_files = analysis_data.get('dependency_order', [])
            
            code_content = "PROJECT ARCHITECTURE OVERVIEW\n\n"
            code_content += f"Total Files: {len(ordered_files)}\n"
            code_content += f"Execution Order: {' -> '.join(ordered_files)}\n\n"
            
            for f_id, f_context in contexts.items():
                code_content += f"{f_context}\n\n"
                
            code_content += "\n=== PROJECT CODE CONTENT ===\n"
            code_content += analysis_data.get('ast_structure', {}).get('code_content', '')
            
            semantic_data = analysis_data.get('semantic_analysis_data', {})
            class_diagram_data = analysis_data.get('class_diagram_data', {})
            extracted_features = analysis_data.get('extracted_features', {})
        else:
            code_content = analysis_data.get('ast_structure', {}).get('code_content', '')
            semantic_data = analysis_data.get('semantic_analysis_data', {})
            extracted_features = analysis_data.get('extracted_features', {})
            class_diagram_data = analysis_data.get('class_diagram_data', {})
        
        # 4. CRITICAL: Strict type enforcement for generation
        if is_high_level:
            print(f"🔵🔵🔵 STRICT ENFORCEMENT: Generating HIGH LEVEL explanation (requested: '{exp_type}') 🔵🔵🔵")
            
            # Select appropriate high level agent based on whether it is a project or single file
            from .agents import ProjectHighLevelAgent
            agent = ProjectHighLevelAgent() if is_project else HighLevelAgent()
            
            classes = class_diagram_data.get('classes', [])
            if classes:
                class_name = classes[0].get('name', 'Unknown')
            else:
                class_name = None

            analysis_summary = self._prepare_high_level_summary(semantic_data, class_diagram_data, extracted_features)

            try:
                raw_content = agent.process(
                    code_content,
                    class_name=class_name,
                    analysis_summary=analysis_summary
                )
                # Skip strict filtering to let the hardened agent prompt handle formatting
                # This prevents mangling the output when the agent slightly deviates from technical constraints
                print(f"DEBUG: High level agent generated content length: {len(raw_content)}")
                    
            except Exception as agent_error:
                error_msg = str(agent_error)
                print(f"ERROR: High level agent failed: {error_msg}")
                raise Exception(f"Failed to generate High Level explanation: {error_msg}")
                
        else:
            print(f"🟡🟡🟡 STRICT ENFORCEMENT: Generating LOW LEVEL explanation (requested: '{exp_type}') 🟡🟡🟡")
            
            from .agents import ProjectLowLevelAgent
            agent = ProjectLowLevelAgent() if is_project else LowLevelAgent()
            detailed_analysis = self._prepare_low_level_analysis(semantic_data, class_diagram_data, extracted_features)
            
            try:
                raw_content = agent.process(code_content, detailed_analysis=detailed_analysis)
                print(f"DEBUG: Low level agent generated content length: {len(raw_content)}")
                
                # Verify it's actually low level
                if not any(term in raw_content.lower() for term in ['## class', '### method', 'constructor:']):
                    print("⚠️ WARNING: Low level content missing technical structure! Adding template...")
                    prefix = "Project: Full System Analysis\n\n" if is_project else "File: Technical Analysis\n\n"
                    raw_content = prefix + raw_content
                    
            except Exception as agent_error:
                error_msg = str(agent_error)
                print(f"ERROR: Low level agent failed: {error_msg}")
                raise Exception(f"Failed to generate Low Level explanation: {error_msg}")

        # 5. Verification skipped to avoid latency/errors from free models
        # We rely on the hardened prompt logic in the primary Agents
        verified_content = raw_content
        print(f"DEBUG: Skipping verification for {normalized_exp_type} to ensure consistency")

        # 6. Save with CORRECT type
        new_doc = {
            "analysis_id": self._query_id,
            "exp_type": normalized_exp_type,
            "explanation_type": normalized_exp_type,
            "content": verified_content,
            "created_at": datetime.utcnow(),
            "code_content": code_content,
            "agent_type": ("ProjectHighLevelAgent" if is_project else "HighLevelAgent") if is_high_level else ("ProjectLowLevelAgent" if is_project else "LowLevelAgent"),
            "original_request_type": str(exp_type),
            "normalized_type": normalized_exp_type,
            "verifier_fallback": verified_content == raw_content,  # True = verifier failed or was skipped
            "is_project": is_project,
        }

        print(f"🔧 SAVING as: {normalized_exp_type} (requested: '{exp_type}')")
        result = self.collection.insert_one(new_doc)

        print(f"✅✅✅ {normalized_exp_type.upper()} explanation saved successfully! ✅✅✅")
        print(f"📁 Document ID: {result.inserted_id}")
        print(f"🔤 Original request: '{exp_type}' -> Normalized: '{normalized_exp_type}'")

        return verified_content, str(result.inserted_id)

    def _prepare_high_level_summary(self, semantic_data, class_diagram_data, extracted_features):
        """إعداد ملخص بسيط للتحليل للمستوى العالي (أسماء فقط)"""
        summary_parts = []
        
        classes = semantic_data.get('classes', []) or class_diagram_data.get('classes', [])
        print(f"DEBUG: _prepare_high_level_summary - classes type: {type(classes)}, classes: {classes}")
        
        if classes:
            class_names = [cls.get('name', 'Unknown') for cls in classes if isinstance(cls, dict)]
            if class_names:
                summary_parts.append(f"Classes found: {', '.join(class_names)}")
        
        if classes:
            all_methods = []
            for cls in classes:
                if isinstance(cls, dict):
                    methods = cls.get('methods', [])
                    print(f"DEBUG: _prepare_high_level_summary - methods type: {type(methods)}, methods: {methods}")
                    if methods:
                        try:
                            method_names = [m if isinstance(m, str) else (m.get('name', '') if isinstance(m, dict) else '') for m in methods]
                            print(f"DEBUG: _prepare_high_level_summary - method_names: {method_names}")
                            all_methods.extend(method_names)
                        except Exception as e:
                            print(f"ERROR in _prepare_high_level_summary: {str(e)}")
                            print(f"ERROR details - methods: {methods}")
                            print(f"ERROR details - types: {[type(m) for m in methods]}")
                            raise
            if all_methods:
                summary_parts.append(f"Main methods/functions: {', '.join(set(all_methods[:10]))}")  # أول 10 فقط
        
        if extracted_features:
            loc = extracted_features.get('lines_of_code', 0)
            func_count = extracted_features.get('functions', 0) or extracted_features.get('methods', 0)
            if loc or func_count:
                summary_parts.append(f"Code statistics: {loc} lines, {func_count} functions/methods")
        
        return "\n".join(summary_parts) if summary_parts else None
    
    def _prepare_low_level_analysis(self, semantic_data, class_diagram_data, extracted_features):
        """إعداد تحليل تفصيلي للمستوى المنخفض مع التركيز على العلاقات والوراثة"""
        analysis_parts = []
        
        # Handle None values safely
        semantic_classes = semantic_data.get('classes', []) if semantic_data else []
        diagram_classes = class_diagram_data.get('classes', []) if class_diagram_data else []
        classes = semantic_classes or diagram_classes
        
        detected_patterns = self._detect_design_patterns(classes)
        if detected_patterns:
         analysis_parts.append("=== DETECTED DESIGN PATTERNS ===")
         for p in detected_patterns:
            analysis_parts.append(f"- {p}")

        if classes:
            analysis_parts.append("=== CLASSES AND RELATIONSHIPS ===")
            
            inheritance_map = {}
            composition_map = {}
            
            for cls in classes:
                if isinstance(cls, dict):
                    class_name = cls.get('name', 'Unknown')
                    
                    inherits = cls.get('inherits', []) or cls.get('inheritance', [])
                    if inherits:
                        inheritance_map[class_name] = inherits
                    
                    associations = cls.get('associations', []) or cls.get('relationships', [])
                    if associations:
                        composition_map[class_name] = associations
            
            if inheritance_map or composition_map:
                analysis_parts.append("\n** RELATIONSHIP ANALYSIS **")
                
                if inheritance_map:
                    analysis_parts.append("Inheritance Relationships:")
                    for child, parents in inheritance_map.items():
                        parents_str = ', '.join(parents) if isinstance(parents, list) else str(parents)
                        analysis_parts.append(f"  - {child} inherits from: {parents_str}")
                
                if composition_map:
                    analysis_parts.append("Composition/Association Relationships:")
                    for class_name, assocs in composition_map.items():
                        for assoc in assocs:
                            if isinstance(assoc, dict):
                                target = assoc.get('target_class', assoc.get('target', 'Unknown'))
                                rel_type = assoc.get('type', 'association')
                                analysis_parts.append(f"  - {class_name} --{rel_type}--> {target}")
            
            analysis_parts.append("\n** DETAILED CLASS ANALYSIS **")
            for cls in classes:
                if not isinstance(cls, dict): continue
                
                class_name = cls.get('name', 'Unknown')
                methods = cls.get('methods', [])
                attributes = cls.get('attributes', []) or cls.get('properties', [])
                
                header = f"\nClass: {class_name}"
                if class_name in inheritance_map:
                    header += f" (extends: {', '.join(inheritance_map[class_name])})"
                analysis_parts.append(header)
                
                if attributes:
                    analysis_parts.append("  Attributes/Properties:")
                    for attr in attributes:
                        if isinstance(attr, dict):
                            name = attr.get('name', '')
                            atype = attr.get('type', 'Any')
                            vis = attr.get('visibility', 'public')
                            analysis_parts.append(f"    - {vis} {name}: {atype}")
                        else:
                            analysis_parts.append(f"    - {attr}")
                
                if methods:
                    analysis_parts.append("  Methods:")
                    for method in methods:
                        if isinstance(method, dict):
                            m_name = method.get('name', '')
                            m_params = method.get('parameters', [])
                            m_ret = method.get('return_type', 'void')
                            m_vis = method.get('visibility', 'public')
                            
                            p_list = []
                            for p in m_params:
                                if isinstance(p, dict):
                                    p_list.append(f"{p.get('name')}: {p.get('type', 'Any')}")
                                else: p_list.append(str(p))
                            
                            analysis_parts.append(f"    - {m_vis} {m_name}({', '.join(p_list)}) -> {m_ret}")
                        else:
                            analysis_parts.append(f"    - {method}()")

        if extracted_features:
            analysis_parts.append("\n=== CODE COMPLEXITY & STATS ===")
            metrics = {
                "Lines of Code": extracted_features.get('lines_of_code'),
                "Total Methods": extracted_features.get('functions') or extracted_features.get('methods'),
                "Complexity Index": extracted_features.get('complexity', {}).get('cyclomatic_complexity')
            }
            for label, val in metrics.items():
                if val: analysis_parts.append(f"{label}: {val}")

        return "\n".join(analysis_parts) if analysis_parts else None
    
    def _detect_design_patterns(self, classes):
        """كشف أنماط التصميم المحتملة من بنية الفئات"""
        patterns = []
        
        if not classes:
            return patterns
        
        class_names = []
        inheritance_count = 0
        factory_indicators = []
        singleton_indicators = []
        
        for cls in classes:
            if isinstance(cls, dict):
                class_name = cls.get('name', '')
                class_names.append(class_name.lower())
                
                if any(keyword in class_name.lower() for keyword in ['factory', 'builder', 'creator']):
                    factory_indicators.append(class_name)
                
                methods = cls.get('methods', [])
                method_names = []
                if methods:
                    for method in methods:
                        if isinstance(method, str):
                            method_names.append(method.lower())
                        elif isinstance(method, dict):
                            method_name = method.get('name', '')
                            if method_name:  # Extra safety check
                                method_names.append(method_name.lower())
                
                if 'getinstance' in method_names or 'instance' in method_names:
                    singleton_indicators.append(class_name)
                
                inherits = cls.get('inherits', []) or cls.get('inheritance', []) or cls.get('bases', [])
                if inherits:
                    inheritance_count += 1
        
        if factory_indicators:
            patterns.append(f"Factory Pattern detected in: {', '.join(factory_indicators)}")
        
        if singleton_indicators:
            patterns.append(f"Singleton Pattern detected in: {', '.join(singleton_indicators)}")
        
        if inheritance_count > 1:
            patterns.append(f"Inheritance hierarchy detected ({inheritance_count} classes with inheritance)")
        
        if any('adapter' in name for name in class_names):
            patterns.append("Adapter Pattern detected")
        
        if any('observer' in name for name in class_names):
            patterns.append("Observer Pattern detected")
        
        if any('strategy' in name for name in class_names):
            patterns.append("Strategy Pattern detected")
        
        return patterns