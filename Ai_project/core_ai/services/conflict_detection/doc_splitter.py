# core_ai/services/conflict_detection/doc_splitter.py
"""
DocSplitter — تقسيم التوثيق وربط كل جزء بالعنصر يلي بيحكي عنه بالكود (DocPrism: Local Context).

split()  : التوثيق (Markdown من الـ agents، أو قاموس منظّم) → أجزاء file / class / method
match()  : ربط الأجزاء بعناصر UnifiedClassDiagram، والناتج 3 قوائم:
           matched       — جزء + العنصر المقابل (هدول بينبعتوا للـ LLM بالخطوة 5)
           unmatched     — جزء بيحكي عن عنصر مش موجود بالكود (مؤشر على توثيق قديم/وعد زايد)
           undocumented  — عناصر بالكود بدون توثيق (تغطية، مش تناقض)

العناوين بتنكتب من الموديل بأشكال مختلفة، فالقواعد متساهلة:
  ### Constructor: public Book(String title, String author, String isbn)
  ### Constructor: Book
  ### Method: setAvailable(self, available: boolean)
  **Method: foo**   /   - Method: `foo(x)`
"""
import re
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from .schemas import ClassDetail, MethodDetail, UnifiedClassDiagram


class DocSnippet(BaseModel):
    scope:              str                     # file | class | method
    file_name:          Optional[str] = None
    class_name:         Optional[str] = None
    member:             Optional[str] = None
    is_constructor:     bool = False
    header_signature:   Optional[str] = None    # التوقيع المكتوب بالعنوان إذا موجود
    header_param_count: Optional[int] = None
    text:               str = ""
    source:             str = "markdown"        # markdown | structured | keyword
    line_start:         Optional[int] = None


class MatchedSnippet(BaseModel):
    snippet:    DocSnippet
    class_name: str
    # أكتر من دالة إذا في overloads والعنوان ما حدّد عدد المعاملات
    methods:    List[MethodDetail] = Field(default_factory=list)


class DocMapping(BaseModel):
    snippets:     List[DocSnippet]           = Field(default_factory=list)
    matched:      List[MatchedSnippet]       = Field(default_factory=list)
    unmatched:    List[DocSnippet]           = Field(default_factory=list)
    undocumented_classes: List[str]          = Field(default_factory=list)
    undocumented_methods: List[Dict[str, str]] = Field(default_factory=list)

    def documented_keys(self) -> Dict[str, set]:
        """بنفس شكل مفاتيح CodeDocConsistencyChecker: classes={'book'}, methods={'book.gettitle'}"""
        classes, methods = set(), set()
        for m in self.matched:
            classes.add(m.class_name.lower())
            for meth in m.methods:
                methods.add(f"{m.class_name}.{meth.name}".lower())
        return {"classes": classes, "methods": methods}


# ─────────────────────────────────────────────────────────────────────
# أنماط العناوين
# ─────────────────────────────────────────────────────────────────────

_PREFIX = r'^\s*(?P<hashes>#{1,6})?\s*(?:[-*]\s+)?(?:\*\*\s*)?'
_FILE_RE   = re.compile(r'^\s*#{1,6}\s*(?:\*\*\s*)?File\s*:\s*(?P<v>.+?)\s*$', re.I)
_CLASS_RE  = re.compile(_PREFIX + r'(?:Class|Interface)\s*:\s*(?P<v>.+?)\s*$', re.I)
_MEMBER_RE = re.compile(_PREFIX + r'(?P<kind>Method|Constructor|Function)\s*:\s*(?P<v>.+?)\s*$', re.I)
_HEADING_RE = re.compile(r'^\s*(#{1,6})\s+\S')
_IDENT_RE  = re.compile(r'[A-Za-z_]\w*')

_MODIFIERS = {"public", "private", "protected", "static", "final", "abstract", "async",
              "def", "function", "override", "virtual", "internal", "synchronized", "void"}
_CTOR_NAMES = {"__init__", "constructor"}
_STRUCTURED_KEYS = {"signature", "description", "raises", "returns"}


def _clean(v: str) -> str:
    return v.replace("**", "").replace("`", "").strip()


def _base_name(name: str) -> str:
    """Zoo<T> → zoo ، Book → book"""
    return re.split(r'[<\[(\s]', name.strip(), 1)[0].lower()


def _split_top_level(text: str) -> List[str]:
    parts, depth, cur = [], 0, []
    for ch in text:
        if ch in "([{<":
            depth += 1
        elif ch in ")]}>":
            depth -= 1
        if ch == "," and depth == 0:
            parts.append("".join(cur)); cur = []
        else:
            cur.append(ch)
    if "".join(cur).strip():
        parts.append("".join(cur))
    return parts


def parse_member_header(value: str) -> Dict[str, Any]:
    """'public Book(String title, String author)' → name=Book, signature=..., param_count=2"""
    v = _clean(value)
    if "(" in v:
        before, _, rest = v.partition("(")
        idents = [t for t in _IDENT_RE.findall(before) if t.lower() not in _MODIFIERS]
        name = idents[-1] if idents else None
        inner = rest.rsplit(")", 1)[0] if ")" in rest else rest
        params = [p for p in _split_top_level(inner) if p.strip()]
        params = [p for p in params if re.split(r'[:=\s]', p.strip(), 1)[0] not in ("self", "cls")]
        return {"name": name, "signature": v, "param_count": len(params)}
    idents = [t for t in _IDENT_RE.findall(v) if t.lower() not in _MODIFIERS]
    return {"name": idents[0] if idents else None, "signature": None, "param_count": None}


class DocSplitter:

    # ─────────────────────────────────────────────────────────────────
    # split
    # ─────────────────────────────────────────────────────────────────

    @staticmethod
    def split(explanation: Any) -> List[DocSnippet]:
        """explanation: نص، أو dict فيه content/explanation، أو قاموس منظّم {"Class.method": {...}}"""
        if isinstance(explanation, str):
            return DocSplitter.split_markdown(explanation)
        explanation = explanation or {}
        snippets = DocSplitter.split_structured(explanation)
        text = explanation.get("content") or explanation.get("explanation") or ""
        if isinstance(text, str) and text.strip():
            snippets = DocSplitter.split_markdown(text) + snippets
        return snippets

    @staticmethod
    def split_markdown(text: str) -> List[DocSnippet]:
        snippets: List[DocSnippet] = []
        file_name: Optional[str] = None
        current: Optional[DocSnippet] = None
        file_snip: Optional[DocSnippet] = None
        class_name: Optional[str] = None
        class_level: Optional[int] = None   # مستوى عنوان الكلاس (عدد الـ #)

        def file_snippet(line_no: int) -> DocSnippet:
            nonlocal file_snip
            if file_snip is None:
                file_snip = DocSnippet(scope="file", file_name=file_name, line_start=line_no)
                snippets.append(file_snip)
            return file_snip

        for i, line in enumerate(text.splitlines(), 1):
            m = _FILE_RE.match(line)
            if m:
                file_name, file_snip, class_name, class_level = _clean(m.group("v")), None, None, None
                current = file_snippet(i)
                continue

            m = _CLASS_RE.match(line)
            if m and not _MEMBER_RE.match(line):
                ids = _IDENT_RE.findall(_clean(m.group("v")))
                if ids:
                    class_name = ids[0]
                    class_level = len(m.group("hashes") or "") or None
                    current = DocSnippet(scope="class", file_name=file_name, class_name=class_name, line_start=i)
                    snippets.append(current)
                    continue

            m = _MEMBER_RE.match(line)
            if m:
                h = parse_member_header(m.group("v"))
                if h["name"]:
                    is_ctor = m.group("kind").lower() == "constructor" or h["name"] in _CTOR_NAMES
                    current = DocSnippet(
                        scope="method", file_name=file_name, class_name=class_name,
                        member=h["name"], is_constructor=is_ctor,
                        header_signature=h["signature"], header_param_count=h["param_count"],
                        line_start=i,
                    )
                    snippets.append(current)
                    continue

            # عنوان عادي بنفس مستوى الكلاس أو أعلى (## Global Recommendations) → رجعنا لمستوى الملف
            hm = _HEADING_RE.match(line)
            if hm and class_name is not None and class_level and len(hm.group(1)) <= class_level:
                class_name, class_level = None, None
                current = file_snippet(i)

            if current is None:
                current = file_snippet(i)
            if line.strip() == "---":
                continue
            current.text += line + "\n"

        for s in snippets:
            s.text = s.text.strip()
        return [s for s in snippets if s.scope != "file" or s.text]

    @staticmethod
    def split_structured(explanation: Dict[str, Any]) -> List[DocSnippet]:
        """{"Class.method": {"signature": ..., "description": ..., "raises": [...]}}"""
        snippets = []
        for key, val in explanation.items():
            if not isinstance(key, str) or not isinstance(val, dict) or not (_STRUCTURED_KEYS & set(val)):
                continue
            body = "\n".join(f"{k}: {v}" for k, v in val.items() if v not in (None, "", []))
            parts = key.split(".")
            if len(parts) >= 2:
                sig = val.get("signature") or None
                h = parse_member_header(sig) if sig else {"param_count": None}
                snippets.append(DocSnippet(
                    scope="method", class_name=parts[0], member=parts[-1],
                    is_constructor=parts[-1] in _CTOR_NAMES or parts[-1] == parts[0],
                    header_signature=sig, header_param_count=h["param_count"],
                    text=body, source="structured",
                ))
            else:
                snippets.append(DocSnippet(scope="class", class_name=key, text=body, source="structured"))
        return snippets

    # ─────────────────────────────────────────────────────────────────
    # match
    # ─────────────────────────────────────────────────────────────────

    @staticmethod
    def match(snippets: List[DocSnippet], diagram: UnifiedClassDiagram,
              full_text: str = "") -> DocMapping:
        classes = {_base_name(c.name): c for c in diagram.classes}
        mapping = DocMapping(snippets=list(snippets))

        has_structure = any(s.scope in ("class", "method") for s in snippets)
        if not has_structure and full_text.strip():
            # ما في عناوين → بحث بأسماء الدوال بالنص (fallback)
            extra = DocSplitter._keyword_snippets(full_text, diagram)
            mapping.snippets.extend(extra)
            snippets = list(snippets) + extra

        documented_methods = set()   # id(MethodDetail)
        documented_classes = set()

        for s in snippets:
            if s.scope == "file":
                continue
            cls = DocSplitter._find_class(s, classes)
            if cls is None:
                mapping.unmatched.append(s)
                continue
            if s.scope == "class":
                mapping.matched.append(MatchedSnippet(snippet=s, class_name=cls.name))
                documented_classes.add(cls.name)
                continue
            methods = DocSplitter._find_methods(s, cls)
            if not methods:
                mapping.unmatched.append(s)
                continue
            mapping.matched.append(MatchedSnippet(snippet=s, class_name=cls.name, methods=methods))
            documented_classes.add(cls.name)
            documented_methods.update(id(m) for m in methods)

        for c in diagram.classes:
            if c.name not in documented_classes:
                mapping.undocumented_classes.append(c.name)
            for m in c.methods:
                if id(m) not in documented_methods:
                    mapping.undocumented_methods.append({"class": c.name, "method": m.name})
        return mapping

    @staticmethod
    def _find_class(s: DocSnippet, classes: Dict[str, ClassDetail]) -> Optional[ClassDetail]:
        if s.class_name:
            return classes.get(_base_name(s.class_name))
        # دالة بدون عنوان كلاس → أول كلاس فيه دالة بهالاسم
        for cls in classes.values():
            if DocSplitter._find_methods(s, cls):
                return cls
        return None

    @staticmethod
    def _find_methods(s: DocSnippet, cls: ClassDetail) -> List[MethodDetail]:
        member = (s.member or "").lower()
        is_ctor = s.is_constructor or member == _base_name(cls.name) or member in _CTOR_NAMES
        candidates = [m for m in cls.methods if m.is_constructor] if is_ctor else []
        if not candidates:
            candidates = [m for m in cls.methods if m.name.lower() == member]
        if len(candidates) > 1 and s.header_param_count is not None:
            by_count = [m for m in candidates
                        if m.parameters is not None and len(m.parameters) == s.header_param_count]
            if by_count:
                candidates = by_count[:1]
        return candidates

    @staticmethod
    def _keyword_snippets(text: str, diagram: UnifiedClassDiagram) -> List[DocSnippet]:
        """لكل دالة اسمها مذكور بالنص: الفقرات يلي فيها الاسم بتصير جزء إلها."""
        paragraphs = [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip()]
        out = []
        for cls in diagram.classes:
            for m in cls.methods:
                pat = re.compile(rf'\b{re.escape(m.name)}\b')
                hits = [p for p in paragraphs if pat.search(p)]
                if hits:
                    out.append(DocSnippet(scope="method", class_name=cls.name, member=m.name,
                                          is_constructor=m.is_constructor,
                                          text="\n\n".join(hits), source="keyword"))
        return out
