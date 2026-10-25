"""
method_details.py
=================
أدوات مشتركة لاستخراج "جسم الدالة" (body) وبصمته بين كل الـ processors.

- body       : نص الجسم القابل للقراءة (بيتقص إذا طويل كتير)
- body_hash  : بصمة للجسم بعد التطبيع — تعليق أو مسافات زيادة ما بيغيّروها،
               أي تغيير بالمنطق بيغيّرها. محسوبة على الجسم الكامل حتى لو انقص.
"""

import hashlib
from typing import Any, Dict, Optional, Tuple

# حد أعلى لطول الـ body المخزّن (البصمة دايماً على الكامل)
MAX_BODY_CHARS = 20000

_TS_COMMENT_TYPES = {"comment", "line_comment", "block_comment", "multiline_comment"}


def hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def cap_body(text: str) -> Tuple[str, bool]:
    if len(text) > MAX_BODY_CHARS:
        return text[:MAX_BODY_CHARS], True
    return text, False


def body_fields(readable: Optional[str], normalized: Optional[str]) -> Dict[str, Any]:
    """يبني حقول body / body_hash / body_truncated. None = ما في جسم (abstract / interface)."""
    if readable is None or normalized is None:
        return {"body": None, "body_hash": None, "body_truncated": False}
    body, truncated = cap_body(readable)
    return {"body": body, "body_hash": hash_text(normalized), "body_truncated": truncated}


# ─────────────────────────────────────────────────────────────────────
# tree-sitter
# ─────────────────────────────────────────────────────────────────────

def _ts_text(node) -> str:
    return node.text.decode("utf-8", errors="replace") if node is not None and node.text else ""


def ts_normalized_tokens(node) -> str:
    """كل الـ tokens (الأوراق) بدون تعليقات، مفصولة بمسافة واحدة."""
    tokens = []
    stack = [node]
    while stack:
        n = stack.pop()
        if n.type in _TS_COMMENT_TYPES:
            continue
        if n.child_count == 0:
            t = _ts_text(n).strip()
            if t:
                tokens.append(t)
        else:
            stack.extend(reversed(n.children))
    return " ".join(tokens)


def ts_body_fields(body_node) -> Dict[str, Any]:
    if body_node is None:
        return body_fields(None, None)
    return body_fields(_ts_text(body_node), ts_normalized_tokens(body_node))


def ts_leading_doc(decl_node) -> Optional[str]:
    """التوثيق يلي قبل التعريف مباشرة: Javadoc / JSDoc (/** ... */) أو C# (/// على كذا سطر)."""
    prev = decl_node.prev_named_sibling if decl_node is not None else None
    if prev is None or prev.type not in _TS_COMMENT_TYPES:
        return None
    text = _ts_text(prev).strip()
    if text.startswith("/**"):
        return text
    if text.startswith("///"):
        lines = []
        while prev is not None and prev.type in _TS_COMMENT_TYPES and _ts_text(prev).strip().startswith("///"):
            lines.append(_ts_text(prev).strip())
            prev = prev.prev_named_sibling
        return "\n".join(reversed(lines))
    return None
