# test_semantic.py
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core_ai.services.conflict_detection.semantic_analyzer import SemanticAnalyzer

diagram_a = {
    "language": "python",
    "classes": [
        {
            "name": "UserService",
            "type": "class",
            "methods": [
                {
                    "name": "remove_user",
                    "signature": "remove_user(user_id: int) -> bool",
                    "visibility": "public",
                    "is_constructor": False,
                    "is_abstract": False
                }
            ],
            "attributes": [],
            "relationships": []
        }
    ]
}

diagram_b = {
    "language": "python",
    "classes": [
        {
            "name": "UserService",
            "type": "class",
            "methods": [
                {
                    "name": "remove_user",
                    "signature": "remove_user(user_id: int, permanent: bool) -> bool",
                    "visibility": "public",
                    "is_constructor": False,
                    "is_abstract": False
                }
            ],
            "attributes": [],
            "relationships": []
        }
    ]
}

analyzer = SemanticAnalyzer()
conflicts = analyzer.analyze(diagram_a, diagram_b)

print("=== عدد التناقضات المكتشفة ===")
print(len(conflicts))
print("\n=== التفاصيل ===")
for c in conflicts:
    if hasattr(c, "model_dump_json"):
        print(c.model_dump_json(indent=2))
    elif hasattr(c, "json"):
        print(c.json(indent=2))
    else:
        print(c)