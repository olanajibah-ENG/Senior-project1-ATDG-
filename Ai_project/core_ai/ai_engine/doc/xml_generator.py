"""
xml_generator.py ← معدّل
XML منظّم ومقروء — نفس بنية PDF من حيث الأقسام والمحتوى
"""

import re
import logging
import datetime
from core_ai.ai_engine.doc.doc_generator import DocumentationGenerator

logger = logging.getLogger(__name__)


class XMLGenerator(DocumentationGenerator):

    def _format_output(self, content: str, data: dict) -> str:
        content_str = str(content) if content else ""
        image_url   = data.get('image_url', '') if data else ''

        # اسم الملف
        filename = "Analysis Report"
        fn_match = re.search(r'File[:\s]+([^\s\n]+)', content_str)
        if fn_match:
            filename = fn_match.group(1).strip()

        explanation_type = data.get('explanation_type', 'high_level') if data else 'high_level'
        exp_label = "Executive Overview" if explanation_type == 'high_level' else "Technical Documentation"
        generated_at = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

        # تنظيف المحتوى
        clean = content_str
        clean = clean.replace("\\'", "'").replace('\\"', '"')
        clean = re.sub(r'^File[:\s]+.*?\n', '', clean, flags=re.MULTILINE)

        # تقسيم لـ sections
        sections = self._parse_sections(clean)

        # بناء XML
        lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<report>',
            '',
            '  <!-- ═══════════════ METADATA ═══════════════ -->',
            '  <metadata>',
            f'    <title>{self._e(filename)}</title>',
            f'    <explanation_type>{self._e(exp_label)}</explanation_type>',
            f'    <generated_at>{generated_at}</generated_at>',
            f'    <generator>AutoTest &amp; DocGen</generator>',
        ]

        if image_url:
            lines.append(f'    <diagram_url>{self._e(image_url)}</diagram_url>')

        lines += [
            '  </metadata>',
            '',
            '  <!-- ═══════════════ CONTENT ═══════════════ -->',
            '  <content>',
        ]

        for i, sec in enumerate(sections):
            level  = sec['level']
            title  = sec['title']
            body   = sec['body'].strip()
            indent = '    '

            # تحديد نوع الـ section
            sec_type = 'overview'
            if level == 2:
                if 'class' in title.lower():
                    sec_type = 'class'
                elif any(k in title.lower() for k in ['method', 'function', 'constructor']):
                    sec_type = 'method'
                else:
                    sec_type = 'section'
            elif level == 3:
                sec_type = 'method'
            elif level == 1:
                sec_type = 'chapter'

            lines.append(f'{indent}<section index="{i+1}" level="{level}" type="{sec_type}">')
            lines.append(f'{indent}  <title>{self._e(title)}</title>')

            if body:
                # تقسيم الـ body لـ sub-elements لو فيه مفاتيح معروفة
                keys_found, remaining = self._extract_keys(body)

                if keys_found:
                    lines.append(f'{indent}  <details>')
                    for k, v in keys_found.items():
                        safe_key = k.lower().replace(' ', '_').replace('&', 'and')
                        lines.append(f'{indent}    <{safe_key}><![CDATA[{v.strip()}]]></{safe_key}>')
                    lines.append(f'{indent}  </details>')

                if remaining.strip():
                    lines.append(f'{indent}  <body><![CDATA[{remaining.strip()}]]></body>')

            lines.append(f'{indent}</section>')

        if data and data.get('code_content'):
            code = data['code_content'][:50000]
            lines += [
                '',
                '  <!-- ═══════════════ SOURCE CODE ═══════════════ -->',
                '  <source_code>',
                f'    <filename>{self._e(filename)}</filename>',
                f'    <content><![CDATA[{code}]]></content>',
                '  </source_code>',
            ]

        lines += [
            '  </content>',
            '',
            '</report>',
        ]

        return '\n'.join(lines)

    def _export(self, formatted_output: str, data: dict) -> bytes:
        return formatted_output.encode('utf-8')

    def _e(self, text: str) -> str:
        """XML escape"""
        if not text:
            return ""
        return (str(text)
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&apos;'))

    def _parse_sections(self, content: str) -> list:
        pattern = re.compile(r'^(#{1,4})\s+(.+)$', re.MULTILINE)
        matches = list(pattern.finditer(content))

        if not matches:
            return [{'level': 1, 'title': 'Content', 'body': content.strip()}]

        sections = []
        if matches[0].start() > 0:
            intro = content[:matches[0].start()].strip()
            if intro:
                sections.append({'level': 0, 'title': 'Introduction', 'body': intro})

        for i, match in enumerate(matches):
            level = len(match.group(1))
            title = match.group(2).strip()
            start = match.end()
            end   = matches[i + 1].start() if i + 1 < len(matches) else len(content)
            body  = content[start:end].strip()
            sections.append({'level': level, 'title': title, 'body': body})

        return sections

    def _extract_keys(self, body: str):
        """يستخرج المفاتيح المعروفة من الـ body ويرجعهم منفصلين"""
        keys = [
            'Purpose', 'Description', 'Parameters', 'Returns',
            'Logic Flow', 'Complexity Level', 'Dependencies',
            'Error Handling', 'Best Practices', 'Security Note',
            'Key Capabilities', 'Main Components', 'Relationships',
            'Attributes', 'Executive Summary',
        ]
        found = {}
        remaining = body

        for key in keys:
            pattern = rf'\*\*{re.escape(key)}:\*\*\s*([^\n*]+(?:\n(?!\*\*)[^\n*]+)*)'
            match = re.search(pattern, remaining, re.IGNORECASE)
            if match:
                found[key] = match.group(1).strip()
                remaining = remaining[:match.start()] + remaining[match.end():]

        # تنظيف Markdown من الـ remaining
        remaining = re.sub(r'\*\*([^*]+)\*\*', r'\1', remaining)
        remaining = re.sub(r'`([^`]+)`', r'\1', remaining)
        remaining = re.sub(r'\n{3,}', '\n\n', remaining)

        return found, remaining