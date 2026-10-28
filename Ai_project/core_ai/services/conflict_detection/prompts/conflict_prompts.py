"""
conflict_prompts.py - Prompts for AI conflict detection
Contains prompts used by the semantic analyzer for detecting conflicts
"""

SEMANTIC_PROMPT = """
You are a senior software architect specializing in detecting semantic and behavioral conflicts between code versions.

Analyze the following two class diagrams and identify semantic conflicts, behavioral changes, and potential issues.

Diagram A (Previous Version):
{diagram_a}

Diagram B (Current Version):
{diagram_b}

---

**Instructions (Fusion Reasoning):**

Use **Fusion Analysis** technique:
1. First, analyze each diagram independently.
2. Then fuse the two analyses together to detect differences, conflicts, and implications.
3. Think step by step deeply before concluding.

**Step-by-step Fusion Process:**
- Compare classes, methods, constructors, interfaces, and relationships.
- Detect removed, added, or modified elements.
- Evaluate behavioral and semantic impact.
- Assign accurate confidence scores.

**After completing your Fusion Analysis**, return **ONLY** valid JSON in this exact format:

```json
{{
    "conflicts": [
        {{
            "type": "behavior_change|logic_change|breaking_change|new_feature|refactoring",
            "severity": "low|medium|high|critical",
            "class_name": "name_of_the_affected_class",
            "member": "method_or_property_name_or_null_for_class_level",
            "description": "clear description of the conflict",
            "old_value": "previous implementation or behavior",
            "new_value": "new implementation or behavior",
            "recommendation": "suggested fix or mitigation",
            "confidence": 0.85
        }}
    ]
}}
### Examples:

**Example 1: Method Signature Change**
Input: removeUser(id) → removeUser(id, permanent: bool)
Output:
{
  "conflicts": [{
    "type": "breaking_change",
    "severity": "high",
    "class_name": "UserService",
    "member": "removeUser",
    "description": "Added new required parameter 'permanent'",
    "old_value": "removeUser(id)",
    "new_value": "removeUser(id, permanent: bool)",
    "impact": "All existing calls will break at compile time",
    "recommendation": "Add overload or default value",
    "confidence": 0.95
  }]
}

**Example 2: Class Removed**
{
  "conflicts": [{
    "type": "removed_class",
    "severity": "critical",
    "class_name": "OldPaymentProcessor",
    "member": null,
    "description": "Class completely removed",
    "old_value": "Class existed with full implementation",
    "new_value": "Class no longer exists",
    "impact": "All references will cause compilation errors",
    "recommendation": "Migrate to NewPaymentService",
    "confidence": 1.0
  }]
}

Now analyze the actual diagrams:


Analyze ALL of the following — do not skip any category:

1.  Method signature changes (parameter count, types, return type).
2.  Return type changes that break existing callers
     (e.g. void → Task/Promise means all callers must now await).
3.  Logic or behavior changes inside methods.
4.  API contract violations.
5.  Data integrity issues.
6.  Performance regressions.
7.  Security vulnerabilities introduced.
8.  CLASSES COMPLETELY REMOVED — a class present in Diagram A but absent in Diagram B
     is a critical breaking change; all usages will fail immediately.
9.  CLASSES COMPLETELY ADDED — a class in B absent in A is a new feature;
     note if it replaces a removed class.
10. Generic type constraint changes
     (e.g. adding new() forces all type-arguments to have a default constructor;
      adding an interface constraint forces callers to use only implementing types).
11. Constructor signature changes — changing parameters of a constructor
     breaks every instantiation site.
12. Interface changes — adding a required method to an interface
     breaks every implementing class.
13. Async/await contract changes — converting a sync method to async
     (void → Task, or adding async modifier) is a breaking change for all callers.
14. RENAME: If member absent in B but similar signature exists (≥70%), report type=RENAMED not REMOVED.

Be thorough but practical — focus on conflicts that would actually impact the system at runtime or compile time.

IMPORTANT: If NO conflicts exist, return exactly: {"conflicts": []}
Do NOT invent conflicts.
"""


# ─────────────────────────────────────────────────────────────────────────────
# Code vs Doc (الخطوة 4)
#
# مبني على prompt ورقة DocPrism (LCEF، github.com/SnowPhoebe/DocPrism، MIT):
# ملخص للتوثيق وللكود، وبعدين 3 أسئلة مستقلة، ولكل "نعم" نسخ حرفي للجملة من التوثيق
# والسطر من الكود. الإضافات عليه:
#   - درجة ثقة لكل نتيجة (METAMON)            - أرقام أسطر بالكود
#   - كذا بند (دالة) بطلب واحد لكل كلاس       - بند للكلاس نفسه (ادعاءات عامة)
# ما في أمثلة جاهزة (few-shot) — متل DocPrism، ولحتى ما يتعلّم الموديل حالات من بيانات القياس.
#
# الأسئلة الثلاثة ← تصنيف DocPrism:
#   not_implemented ← Over_Promise    conflicting ← Direct_Mismatch    undocumented ← Under_Promise
# ─────────────────────────────────────────────────────────────────────────────

CODE_DOC_SYSTEM = """You are a code review expert who identifies inconsistencies between source code and its documentation.
You only report what you can verify from the given code and documentation. Respond with valid JSON only, no markdown."""

CODE_DOC_PROMPT = """You are reviewing {language} code from the class `{class_name}` against its documentation.

Each ITEM below contains one function (or constructor) with its own documentation, or the
class itself with its general documentation and its list of members. Analyze every ITEM
independently: judge a function only against its own documentation.

{items}

For EACH item answer three independent questions:

1. not_implemented: Does the documentation claim a behavior or guarantee that the code does
   not implement at all? (For a CLASS item: does the documentation claim a capability that no
   member of the class provides?)
2. conflicting: Does the code do something DIFFERENT from what the documentation states about
   the same thing (return value, exception, parameter, default value, condition, unit, example)?
3. undocumented: Does the code have behavior a caller needs to know that the documentation does
   not mention (an exception thrown, a special return value such as null/None, a side effect)?

Rules:
- Judge only specific claims. General or vague statements are not inconsistencies.
- Missing low-level detail in short documentation is not an inconsistency.
- If the code does something else instead of the claim, it is "conflicting"; if the code does
  nothing about the claim, it is "not_implemented".
- Copy "doc_snippet" and "code_snippet" EXACTLY (verbatim) from the input; do not paraphrase.
- "code_lines" are the line numbers shown at the left of the code.
- "confidence" is your confidence (0.0 to 1.0) that the finding is a real inconsistency.
- If there is nothing to report for a question, return an empty list for it.

Return ONLY this JSON:
{{
  "results": [
    {{
      "id": "<item id>",
      "documentation_summary": "...",
      "code_summary": "...",
      "not_implemented": [{{"doc_snippet": "...", "explanation": "...", "confidence": 0.0}}],
      "conflicting": [{{"doc_snippet": "...", "code_snippet": "...", "code_lines": [0], "explanation": "...", "confidence": 0.0}}],
      "undocumented": [{{"code_snippet": "...", "code_lines": [0], "explanation": "...", "confidence": 0.0}}]
    }}
  ]
}}"""

CODE_DOC_METHOD_ITEM = """ITEM id={item_id}
[CODE]
{code}
[/CODE]
[DOCUMENTATION]
{doc}
[/DOCUMENTATION]"""

CODE_DOC_CLASS_ITEM = """ITEM id={item_id}  (the class itself)
[MEMBERS]
{members}
[/MEMBERS]
[DOCUMENTATION]
{doc}
[/DOCUMENTATION]"""
