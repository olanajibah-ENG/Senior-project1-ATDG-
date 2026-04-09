"""
xml_generator.py  ← جديد كلياً
================
XMLGenerator — يولّد ملف XML منظّم يحتوي المحتوى كاملاً.
مفيد للتكامل مع أنظمة خارجية أو لتبادل البيانات.

البنية:
    <documentation>
        <metadata> ... </metadata>
        <content>
            <section> ... </section>
            ...
        </content>
    </documentation>
"""

import re
import logging
import datetime
from core_ai.ai_engine.doc.doc_generator import DocumentationGenerator

logger = logging.getLogger(__name__)


class XMLGenerator(DocumentationGenerator):

    def _format_output(self, content: str, data: dict) -> str:
        """
        يحوّل المحتوى لـ XML منظّم.
        كل section (عنوان + نص تحته) تصير عنصر <section> منفصل.
        """
        content_str = str(content) if content else ""

        explanation_type = data.get('explanation_type') if data else None
        exp_type_display = "high_level" if explanation_type == 'high_level' else "low_level"
        created_at = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

        filename = ""
        if data:
            filename = data.get('filename') or data.get('original_filename') or ""
        if not filename:
            file_match = re.search(r'File:\s*([^\s\n]+)', content_str)
            if file_match:
                filename = file_match.group(1)

        image_url = data.get('image_url', '') if data else ''

        # تقسيم المحتوى لـ sections بناءً على العناوين
        sections = self._parse_sections(content_str)

        # بناء XML
        xml_parts = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<documentation>',
            '  <metadata>',
            f'    <title>{self._escape(filename or "Technical Documentation")}</title>',
            f'    <type>{self._escape(exp_type_display)}</type>',
            f'    <generated_at>{created_at}</generated_at>',
            f'    <generator>AutoTest &amp; DocGen</generator>',
        ]

        if image_url:
            xml_parts.append(f'    <diagram_url>{self._escape(image_url)}</diagram_url>')

        xml_parts += [
            '  </metadata>',
            '  <content>',
        ]

        for i, section in enumerate(sections):
            level   = section['level']
            title   = section['title']
            body    = section['body'].strip()
            indent  = '    '
            xml_parts.append(f'{indent}<section level="{level}" index="{i+1}">')
            xml_parts.append(f'{indent}  <title>{self._escape(title)}</title>')
            if body:
                xml_parts.append(f'{indent}  <body><![CDATA[{body}]]></body>')
            xml_parts.append(f'{indent}</section>')

        xml_parts += [
            '  </content>',
            '</documentation>',
        ]

        return '\n'.join(xml_parts)

    def _export(self, formatted_output: str, data: dict) -> bytes:
        """يرجع XML كـ UTF-8 bytes."""
        return formatted_output.encode('utf-8')

    # ── helpers ──────────────────────────────────────────────────────────────
    def _escape(self, text: str) -> str:
        """يعمل XML escaping للنص."""
        if not text:
            return ""
        text = str(text)
        text = text.replace('&', '&amp;')
        text = text.replace('<', '&lt;')
        text = text.replace('>', '&gt;')
        text = text.replace('"', '&quot;')
        text = text.replace("'", '&apos;')
        return text

    def _parse_sections(self, content: str) -> list:
        """
        يقسّم المحتوى لـ sections بناءً على عناوين Markdown (# ## ###).
        كل section عندها: level, title, body.
        """
        sections = []
        # نبحث عن العناوين
        pattern = re.compile(r'^(#{1,4})\s+(.+)$', re.MULTILINE)
        matches = list(pattern.finditer(content))

        if not matches:
            # لو ما في عناوين → كل المحتوى section واحد
            sections.append({
                'level': 1,
                'title': 'Content',
                'body':  content.strip(),
            })
            return sections

        # المحتوى قبل أول عنوان
        if matches[0].start() > 0:
            intro = content[:matches[0].start()].strip()
            if intro:
                sections.append({'level': 0, 'title': 'Introduction', 'body': intro})

        for i, match in enumerate(matches):
            level = len(match.group(1))
            title = match.group(2).strip()
            # الـ body هو المحتوى بين هاد العنوان والعنوان التالي
            start = match.end()
            end   = matches[i + 1].start() if i + 1 < len(matches) else len(content)
            body  = content[start:end].strip()
            sections.append({'level': level, 'title': title, 'body': body})

        return sections