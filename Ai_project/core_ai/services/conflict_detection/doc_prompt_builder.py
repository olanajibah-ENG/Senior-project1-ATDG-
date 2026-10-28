# core_ai/services/conflict_detection/doc_prompt_builder.py
"""
بيجهّز طلبات الـ LLM للكود مقابل التوثيق (الخطوة 4) من ناتج DocSplitter (الخطوة 3).

- طلب واحد لكل كلاس، فيه بند (ITEM) لكل دالة موثّقة: كودها مع أرقام الأسطر + توثيقها هي بس.
- بند للكلاس نفسه إذا في توثيق عام (قسم الكلاس أو أقسام الملف): مع قائمة الدوال، لحتى ينكشف
  ادعاء متل "بيرجّع اسم المؤلف" لما ما في دالة بتعمل هالشي.
- الكلاس الكبير بينقسم على كذا طلب (MAX_REQUEST_CHARS).

الكود: إذا انعطى الكود الأصلي (source_code) وفي أرقام أسطر للدالة → الأسطر كما هي.
وإلا → منعيد بناء الدالة من حقول الخطوة 1 (المعاملات + نوع الإرجاع + الجسم).
"""
import textwrap
from collections import OrderedDict
from typing import Dict, List, Optional, Tuple

from pydantic import BaseModel, Field

from .doc_splitter import DocMapping, MatchedSnippet
from .prompts.conflict_prompts import (
    CODE_DOC_CLASS_ITEM, CODE_DOC_METHOD_ITEM, CODE_DOC_PROMPT, CODE_DOC_SYSTEM,
)
from .schemas import MODULE_CLASS, MethodDetail, UnifiedClassDiagram

MAX_REQUEST_CHARS = 12000      # حجم الطلب الواحد تقريباً (بدون التعليمات الثابتة)
MAX_ITEM_CODE_LINES = 200      # الدالة الأطول بتنقص وبينذكر هالشي بالطلب


class CodeDocItem(BaseModel):
    id:         str
    class_name: str
    member:     Optional[str] = None          # None = بند الكلاس نفسه
    doc_text:   str                           # للتأكد بالخطوة 5 إنه الجملة المنسوخة موجودة فعلاً
    code_lines: Dict[int, str] = Field(default_factory=dict)   # الأسطر يلي انعرضت (للتأكد من الأسطر المذكورة)


class CodeDocRequest(BaseModel):
    class_name: str
    system:     str
    user:       str
    items:      List[CodeDocItem] = Field(default_factory=list)


# ─────────────────────────────────────────────────────────────────────
# كود الدالة
# ─────────────────────────────────────────────────────────────────────

def _python_header(m: MethodDetail, in_class: bool) -> str:
    parts, saw_kwonly = [], False
    if in_class and "staticmethod" not in m.decorators:
        parts.append("cls" if "classmethod" in m.decorators else "self")
    for p in m.parameters or []:
        text = p.name or "?"
        if p.kind == "var_positional":
            text, saw_kwonly = f"*{text}", True
        elif p.kind == "var_keyword":
            text = f"**{text}"
        elif p.kind == "keyword_only" and not saw_kwonly:
            parts.append("*")
            saw_kwonly = True
        if p.type and p.kind not in ("var_positional", "var_keyword"):
            text += f": {p.type}"
        if p.default is not None:
            text += f" = {p.default}"
        parts.append(text)
    ret = f" -> {m.return_type}" if m.return_type else ""
    prefix = "async def" if m.is_async else "def"
    decorators = "".join(f"@{d}\n" for d in m.decorators)
    return f"{decorators}{prefix} {m.name}({', '.join(parts)}){ret}:"


def _c_like_header(m: MethodDetail) -> str:
    params = ", ".join(f"{p.type} {p.name}".strip() if p.type else (p.name or "?") for p in (m.parameters or []))
    ret = "" if m.is_constructor or not m.return_type else f"{m.return_type} "
    decorators = "".join(f"{d}\n" for d in m.decorators)
    return f"{decorators}{ret}{m.name}({params})"


def reconstruct_method(m: MethodDetail, language: str, in_class: bool = True) -> List[str]:
    if (language or "").lower() == "python":
        body = textwrap.indent(m.body, "    ") if m.body else "    ...  # body unavailable"
        return (_python_header(m, in_class) + "\n" + body).splitlines()
    body = m.body if m.body else "{ /* body unavailable */ }"
    return (_c_like_header(m) + " " + body).splitlines()


def method_lines(m: MethodDetail, language: str, source_lines: Optional[List[str]] = None,
                 in_class: bool = True) -> Tuple[Dict[int, str], bool]:
    """{رقم السطر: السطر} — من الكود الأصلي إذا متوفر، وإلا من إعادة البناء. + هل انقص؟"""
    if source_lines and m.line_start and m.line_end and m.line_end <= len(source_lines):
        lines, first = source_lines[m.line_start - 1:m.line_end], m.line_start
    else:
        lines, first = reconstruct_method(m, language, in_class), 1
    truncated = len(lines) > MAX_ITEM_CODE_LINES or m.body_truncated
    return {first + i: l for i, l in enumerate(lines[:MAX_ITEM_CODE_LINES])}, truncated


def method_code(m: MethodDetail, language: str, source_lines: Optional[List[str]] = None,
                in_class: bool = True) -> str:
    """الكود مع أرقام الأسطر."""
    numbered, truncated = method_lines(m, language, source_lines, in_class)
    out = "\n".join(f"{n:>4} | {l}" for n, l in numbered.items())
    if truncated:
        out += "\n     | ... (code truncated)"
    return out


# ─────────────────────────────────────────────────────────────────────
# بناء الطلبات
# ─────────────────────────────────────────────────────────────────────

def _guess_language(diagram: UnifiedClassDiagram) -> str:
    """إذا اللغة مش مسجّلة بالتحليل: جسم بيبلّش بـ '{' = لغة متل جافا، وإلا بايثون."""
    bodies = [m.body for c in diagram.classes for m in c.methods if m.body]
    if not bodies:
        return ""
    return "java" if sum(b.lstrip().startswith("{") for b in bodies) * 2 >= len(bodies) else "python"


def build_code_doc_requests(mapping: DocMapping, diagram: UnifiedClassDiagram,
                            language: str = "", source_code: Optional[str] = None) -> List[CodeDocRequest]:
    language = language or diagram.language or _guess_language(diagram)
    source_lines = source_code.splitlines() if source_code else None
    classes = {c.name: c for c in diagram.classes}

    # البنود لكل كلاس، بالترتيب
    per_class: "OrderedDict[str, Dict[str, list]]" = OrderedDict()
    def bucket(name):
        return per_class.setdefault(name, {"class_docs": [], "methods": []})

    for ms in mapping.matched:
        if ms.snippet.scope == "class":
            bucket(ms.class_name)["class_docs"].append(ms.snippet.text)
        elif ms.methods:
            bucket(ms.class_name)["methods"].append(ms)

    # الأقسام العامة للملف: بتروح لبند الكلاس إذا في كلاس حقيقي واحد بالملف
    file_docs = [s.text for s in mapping.snippets if s.scope == "file" and s.text.strip()]
    real_classes = [c.name for c in diagram.classes if c.name != MODULE_CLASS]
    if file_docs:
        target = real_classes[0] if len(real_classes) == 1 else (MODULE_CLASS if MODULE_CLASS in classes else None)
        if target:
            bucket(target)["class_docs"][:0] = file_docs

    requests: List[CodeDocRequest] = []
    for class_name, data in per_class.items():
        cls = classes.get(class_name)
        if cls is None:
            continue
        blocks: List[tuple] = []          # (CodeDocItem, text)
        used_ids: Dict[str, int] = {}

        def new_id(base: str) -> str:
            used_ids[base] = used_ids.get(base, 0) + 1
            return base if used_ids[base] == 1 else f"{base}#{used_ids[base]}"

        class_doc = "\n\n".join(d for d in data["class_docs"] if d.strip())
        if class_doc:
            members = "\n".join(f"- {m.signature}" for m in cls.methods) or "(no methods)"
            item = CodeDocItem(id=new_id(class_name), class_name=class_name, doc_text=class_doc)
            blocks.append((item, CODE_DOC_CLASS_ITEM.format(item_id=item.id, members=members, doc=class_doc)))

        for ms in data["methods"]:
            ms: MatchedSnippet
            in_class = class_name != MODULE_CLASS
            code = "\n\n".join(method_code(m, language, source_lines, in_class) for m in ms.methods)
            shown_lines: Dict[int, str] = {}
            for m in ms.methods:
                shown_lines.update(method_lines(m, language, source_lines, in_class)[0])
            item = CodeDocItem(id=new_id(f"{class_name}.{ms.methods[0].name}"), class_name=class_name,
                               member=ms.methods[0].name, doc_text=ms.snippet.text, code_lines=shown_lines)
            blocks.append((item, CODE_DOC_METHOD_ITEM.format(item_id=item.id, code=code, doc=ms.snippet.text)))

        # تقسيم على طلبات بحجم معقول
        chunk, size = [], 0
        for item, text in blocks:
            if chunk and size + len(text) > MAX_REQUEST_CHARS:
                requests.append(_request(class_name, language, chunk))
                chunk, size = [], 0
            chunk.append((item, text))
            size += len(text)
        if chunk:
            requests.append(_request(class_name, language, chunk))
    return requests


def _request(class_name: str, language: str, chunk: List[tuple]) -> CodeDocRequest:
    shown = "the module (functions outside any class)" if class_name == MODULE_CLASS else class_name
    user = CODE_DOC_PROMPT.format(language=language or "source", class_name=shown,
                                  items="\n\n".join(text for _, text in chunk))
    return CodeDocRequest(class_name=class_name, system=CODE_DOC_SYSTEM, user=user,
                          items=[item for item, _ in chunk])
