"""
html_generator.py  ← جديد كلياً
=================
HTMLGenerator — يولّد ملف HTML قابل للعرض في المتصفح مباشرة.

يرث من DocumentationGenerator ويطبّق:
    _format_output() → يبني HTML كامل مع CSS مدمج
    _export()        → يرجع HTML كـ UTF-8 bytes
"""

import re
import logging
import datetime
from core_ai.ai_engine.doc.doc_generator import DocumentationGenerator

logger = logging.getLogger(__name__)


class HTMLGenerator(DocumentationGenerator):

    def _format_output(self, content: str, data: dict) -> str:
        """
        يبني صفحة HTML كاملة مع CSS مدمج.
        المحتوى (Markdown) يتحول لـ HTML داخل الصفحة.
        """
        content_str = str(content) if content else ""

        # نوع الشرح
        explanation_type = data.get('explanation_type') if data else None
        exp_type_display = "Executive Overview" if explanation_type == 'high_level' else "Technical Documentation"

        created_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

        # اسم الملف
        filename = "DOCUMENTATION"
        if data:
            if data.get('filename'):
                filename = data.get('filename').upper()
            elif data.get('original_filename'):
                filename = data.get('original_filename').upper()
        if filename == "DOCUMENTATION":
            file_match = re.search(r'File:\s*([^\s\n]+)', content_str)
            if file_match:
                filename = file_match.group(1).upper()

        # تحويل Markdown → HTML
        html_body = self._markdown_to_html(content_str)

        # diagram
        image_url = data.get('image_url', '') if data else ''
        diagram_html = ""
        if image_url:
            diagram_html = f"""
            <div class="diagram-section">
                <h2>📊 Architecture Visualization</h2>
                <img src="{image_url}" alt="Class Diagram" style="max-width:100%;"/>
            </div>
            <hr/>"""

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8"/>
    <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
    <title>{filename} — {exp_type_display}</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: 'Segoe UI', Arial, sans-serif;
            background: #f4f6f9;
            color: #2c3e50;
            line-height: 1.7;
            padding: 0 0 40px;
        }}
        header {{
            background: linear-gradient(135deg, #1a237e, #283593);
            color: white;
            padding: 32px 48px;
        }}
        header h1 {{ font-size: 2rem; letter-spacing: 1px; }}
        header .meta {{
            margin-top: 10px;
            font-size: 0.9rem;
            opacity: 0.85;
            display: flex;
            gap: 24px;
            flex-wrap: wrap;
        }}
        header .badge {{
            background: rgba(255,255,255,0.15);
            border-radius: 12px;
            padding: 3px 12px;
        }}
        .container {{
            max-width: 960px;
            margin: 40px auto;
            padding: 0 24px;
        }}
        .content-card {{
            background: white;
            border-radius: 12px;
            padding: 40px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.07);
        }}
        h1, h2, h3, h4 {{
            color: #1a237e;
            margin: 28px 0 12px;
            line-height: 1.3;
        }}
        h1 {{ font-size: 1.8rem; border-bottom: 3px solid #1a237e; padding-bottom: 8px; }}
        h2 {{ font-size: 1.4rem; border-left: 4px solid #3949ab; padding-left: 12px; }}
        h3 {{ font-size: 1.15rem; color: #283593; }}
        p {{ margin: 12px 0; }}
        code {{
            background: #f0f4ff;
            color: #c0392b;
            padding: 2px 7px;
            border-radius: 4px;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
        }}
        pre {{
            background: #1e1e2e;
            color: #cdd6f4;
            padding: 20px;
            border-radius: 8px;
            overflow-x: auto;
            margin: 16px 0;
            font-size: 0.88em;
            line-height: 1.6;
        }}
        pre code {{ background: none; color: inherit; padding: 0; }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 16px 0;
            font-size: 0.95em;
        }}
        th {{
            background: #1a237e;
            color: white;
            padding: 10px 14px;
            text-align: left;
        }}
        td {{ padding: 9px 14px; border-bottom: 1px solid #e8ecf0; }}
        tr:nth-child(even) td {{ background: #f8f9ff; }}
        ul, ol {{ padding-left: 24px; margin: 12px 0; }}
        li {{ margin: 6px 0; }}
        blockquote {{
            border-left: 4px solid #3949ab;
            background: #f0f4ff;
            padding: 12px 20px;
            margin: 16px 0;
            border-radius: 0 8px 8px 0;
            color: #455a64;
        }}
        hr {{ border: none; border-top: 1px solid #e0e6ef; margin: 28px 0; }}
        .diagram-section {{ margin: 24px 0; }}
        footer {{
            text-align: center;
            margin-top: 40px;
            font-size: 0.82rem;
            color: #90a4ae;
        }}
    </style>
</head>
<body>
<header>
    <h1>📜 {filename}</h1>
    <div class="meta">
        <span class="badge">✅ VERIFIED</span>
        <span class="badge">📅 {created_at}</span>
        <span class="badge">🏷 {exp_type_display}</span>
        <span class="badge">🤖 AutoTest &amp; DocGen</span>
    </div>
</header>
<div class="container">
    <div class="content-card">
        {diagram_html}
        {html_body}
    </div>
</div>
<footer>
    Generated by <strong>AutoTest &amp; DocGen</strong> — Technical Intelligence Unit<br/>
    Last Updated: {created_at}
</footer>
</body>
</html>"""
        return html

    def _export(self, formatted_output: str, data: dict) -> bytes:
        """يرجع HTML كـ UTF-8 bytes."""
        return formatted_output.encode('utf-8')

    # ── تحويل Markdown → HTML ──────────────────────────────────────────────────
    def _markdown_to_html(self, content: str) -> str:
        """يحوّل Markdown بسيط لـ HTML."""

        # code blocks أولاً (قبل ما نلمس أي شي تاني)
        content = re.sub(
            r'```(?:\w+)?\n(.*?)```',
            lambda m: f'<pre><code>{self._escape_html(m.group(1))}</code></pre>',
            content, flags=re.DOTALL
        )

        # tables
        content = self._process_tables(content)

        lines = content.split('\n')
        html_lines = []
        in_ul = False
        in_ol = False

        for line in lines:
            # headings
            if line.startswith('#### '):
                line = self._close_lists(in_ul, in_ol) + f'<h4>{line[5:]}</h4>'
                in_ul = in_ol = False
            elif line.startswith('### '):
                line = self._close_lists(in_ul, in_ol) + f'<h3>{line[4:]}</h3>'
                in_ul = in_ol = False
            elif line.startswith('## '):
                line = self._close_lists(in_ul, in_ol) + f'<h2>{line[3:]}</h2>'
                in_ul = in_ol = False
            elif line.startswith('# '):
                line = self._close_lists(in_ul, in_ol) + f'<h1>{line[2:]}</h1>'
                in_ul = in_ol = False
            # hr
            elif re.match(r'^---+$', line.strip()):
                line = self._close_lists(in_ul, in_ol) + '<hr/>'
                in_ul = in_ol = False
            # blockquote
            elif line.startswith('> '):
                line = self._close_lists(in_ul, in_ol) + f'<blockquote>{line[2:]}</blockquote>'
                in_ul = in_ol = False
            # unordered list
            elif re.match(r'^[\*\-\+] ', line):
                if not in_ul:
                    line = '<ul><li>' + line[2:] + '</li>'
                    in_ul = True
                else:
                    line = '<li>' + line[2:] + '</li>'
            # ordered list
            elif re.match(r'^\d+\. ', line):
                if not in_ol:
                    line = '<ol><li>' + re.sub(r'^\d+\. ', '', line) + '</li>'
                    in_ol = True
                else:
                    line = '<li>' + re.sub(r'^\d+\. ', '', line) + '</li>'
            # empty line
            elif line.strip() == '':
                close = self._close_lists(in_ul, in_ol)
                in_ul = in_ol = False
                line = close + '<br/>'
            # paragraph
            else:
                close = self._close_lists(in_ul, in_ol)
                in_ul = in_ol = False
                line = close + '<p>' + line + '</p>'

            html_lines.append(line)

        closing = self._close_lists(in_ul, in_ol)
        result = '\n'.join(html_lines) + closing

        # inline formatting
        result = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', result)
        result = re.sub(r'\*(.*?)\*', r'<em>\1</em>', result)
        result = re.sub(r'`(.*?)`', r'<code>\1</code>', result)
        result = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', result)

        return result

    def _close_lists(self, in_ul: bool, in_ol: bool) -> str:
        if in_ul:
            return '</ul>'
        if in_ol:
            return '</ol>'
        return ''

    def _escape_html(self, text: str) -> str:
        return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

    def _process_tables(self, content: str) -> str:
        table_pattern = r'(\|[^\n]+\|\n\|[-\s|:]+\|\n(?:\|[^\n]+\|\n?)*)'
        def table_repl(match):
            rows = match.group(1).strip().split('\n')
            html = ['<table>']
            for i, row in enumerate(rows):
                if i == 1:
                    continue
                tag = 'th' if i == 0 else 'td'
                cells = [c.strip() for c in row.split('|')[1:-1]]
                html.append('<tr>' + ''.join(f'<{tag}>{c}</{tag}>' for c in cells) + '</tr>')
            html.append('</table>')
            return '\n'.join(html)
        return re.sub(table_pattern, table_repl, content)