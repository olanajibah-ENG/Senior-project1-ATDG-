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
