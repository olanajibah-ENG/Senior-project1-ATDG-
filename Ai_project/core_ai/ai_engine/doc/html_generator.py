"""
html_generator.py ← معدّل
نفس تنسيق وألوان PDF بالضبط — CSS مستخرج من pdf.py مباشرة
"""

import re
import logging
import datetime
from core_ai.ai_engine.doc.doc_generator import DocumentationGenerator

logger = logging.getLogger(__name__)


class HTMLGenerator(DocumentationGenerator):

    def _format_output(self, content: str, data: dict) -> str:
        content_str = str(content) if content else ""
        image_url   = data.get('image_url', '') if data else ''

        # اسم الملف — نفس منطق PDF
        filename = "Analysis Report"
        filename_match = re.search(r'File[:\s]+([^\s\n]+)', content_str)
        if filename_match:
            filename = filename_match.group(1).strip()
        safe_filename = filename.replace('<', '&lt;').replace('>', '&gt;')

        generation_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

        # نفس دالة تحويل النص لـ HTML المستخدمة في PDF
        main_content_html = self._convert_text_to_enhanced_html(content_str)

        diagram_html = ""
        if image_url:
            diagram_html = f'<div style="text-align:center;margin-bottom:20px;"><h3>Architecture Visualization</h3><img src="{image_url}" style="width:100%;border:1px solid #ddd;border-radius:10px;"></div>'

        code_section_html = ""
        if data and data.get('code_content'):
            code = data['code_content'].replace('<', '&lt;').replace('>', '&gt;')
            code_section_html = f"""
            <div class="code-section">
                <h3>Source Code Analysis</h3>
                <h4>{safe_filename}</h4>
                <pre class="source-code">{code[:1000000]}</pre>
            </div>"""

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8"/>
    <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
    <title>Technical Analysis Report - {safe_filename}</title>
    <style>
        * {{ box-sizing: border-box; }}

        body {{
            font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
            color: #2d3436;
            line-height: 1.6;
            background: #f4f6f9;
            margin: 0;
            padding: 0;
        }}

        /* ── Cover Page ── */
        .header-centered {{
            text-align: center;
            background: #ffffff;
            padding: 80px 40px 60px;
            box-shadow: 0 10px 20px rgba(0,0,0,0.1);
            margin-bottom: 40px;
        }}
        .logo {{
            color: #5a3d9a;
            font-size: 48px;
            font-weight: 800;
            margin-bottom: 16px;
            letter-spacing: -1px;
            text-shadow: 0 2px 4px rgba(0,0,0,0.15);
        }}
        .logo-accent {{ color: #8e44ad; font-weight: 800; }}
        .subtitle {{
            color: #636e72;
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 2px;
            font-weight: 300;
            margin-top: 8px;
        }}
        .project-title {{
            font-size: 26px;
            color: #2d3436;
            margin-top: 16px;
            font-weight: 500;
        }}
        .generation-date {{
            font-size: 12px;
            color: #b2bec3;
            margin-top: 10px;
            font-weight: 300;
        }}

        /* ── Content wrapper ── */
        .content {{
            max-width: 960px;
            margin: 0 auto;
            padding: 0 24px 60px;
            background: #ffffff;
            box-shadow: 0 2px 12px rgba(0,0,0,0.06);
        }}

        /* ── Typography ── */
        p {{
            margin-bottom: 14px;
            text-align: justify;
            word-wrap: break-word;
        }}

        /* ── High-level section heading ── */
        .high-level-section {{
            color: #2c3e50;
            font-size: 22px;
            border-bottom: 3px solid #5a3d9a;
            padding-bottom: 10px;
            padding-left: 15px;
            margin-top: 40px;
            margin-bottom: 20px;
            font-weight: 600;
            position: relative;
        }}
        .high-level-section::before {{
            content: "";
            position: absolute;
            left: 0; top: 0; bottom: 0;
            width: 4px;
            border-radius: 2px;
            background: #5a3d9a;
        }}

        /* ── Class card ── */
        .class-card {{
            margin-top: 50px;
            page-break-inside: avoid;
        }}
        .class-header {{
            background: linear-gradient(135deg, #4834d4 0%, #341f97 100%);
            padding: 13px 22px;
            display: inline-block;
            border-radius: 0 10px 10px 0;
            margin-top: 20px;
            font-size: 20px;
            color: #ffffff;
            font-weight: 600;
            box-shadow: 0 4px 15px rgba(72,52,212,0.3);
        }}
        .class-content-wrapper {{
            margin-left: 30px;
            padding-left: 25px;
            margin-top: 15px;
        }}

        /* ── Method container ── */
        .method-container {{
            border: 1px solid #e8eaf6;
            border-left: 5px solid #6c5ce7;
            border-radius: 8px;
            margin-top: 25px;
            margin-bottom: 25px;
            background: #fbfbff;
            box-shadow: 0 4px 10px rgba(108,92,231,0.08);
            overflow: hidden;
        }}
        .method-title {{
            color: #ffffff;
            padding: 12px 20px;
            font-size: 15px;
            margin: 0;
            font-weight: 600;
            background: linear-gradient(135deg, #6c5ce7 0%, #a29bfe 100%);
            border-radius: 6px 6px 0 0;
        }}
        .method-description-area {{
            padding: 20px;
            background: transparent;
        }}

        /* ── Detail key ── */
        .detail-key {{
            color: #2980b9;
            font-weight: 700;
            text-transform: uppercase;
            font-size: 11px;
            display: block;
            margin-top: 15px;
            margin-bottom: 5px;
            border-left: 3px solid #3498db;
            padding: 2px 8px;
            background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
            border-radius: 0 6px 6px 0;
            letter-spacing: 0.5px;
            box-shadow: 0 2px 4px rgba(33,150,243,0.1);
        }}
        .key-group {{ margin-top: 15px; margin-bottom: 10px; display: block; }}
        .key-content {{ margin-left: 5px; display: block; }}

        /* ── Highlighted & inline code ── */
        .highlighted-text {{
            color: #a29bfe;
            font-weight: 600;
            background: rgba(162,155,254,0.1);
            padding: 2px 6px;
            border-radius: 4px;
        }}
        .inline-code {{
            background: rgba(162,155,254,0.15);
            color: #6c5ce7;
            padding: 2px 6px;
            border-radius: 4px;
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 90%;
            font-weight: 500;
            border: 1px solid rgba(162,155,254,0.3);
        }}
        code {{
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            color: #2c3e50;
            padding: 3px 8px;
            border-radius: 4px;
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 90%;
            border: 1px solid #e1e8ed;
        }}

        /* ── Source code block ── */
        .source-code {{
            background: #f8f9fa;
            color: #2c3e50;
            padding: 25px;
            border-radius: 8px;
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 12px;
            line-height: 1.6;
            border: 1px solid #dee2e6;
            white-space: pre-wrap;
            word-wrap: break-word;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }}
        .code-section {{
            margin-top: 50px;
            padding-top: 20px;
            border-top: 2px solid #e0e0e0;
        }}
        .code-section h3 {{ color: #2c3e50; font-size: 20px; margin-bottom: 10px; }}
        .code-section h4 {{ color: #7f8c8d; font-size: 13px; margin-bottom: 14px; font-weight: 400; }}

        /* ── Recommendation box ── */
        .recommendation-box {{
            background: #f3f0ff;
            border-left: 5px solid #6c5ce7;
            padding: 15px;
            margin-top: 20px;
            border-radius: 0 10px 10px 0;
            font-style: italic;
            color: #4834d4;
            box-shadow: 0 2px 8px rgba(108,92,231,0.1);
        }}

        /* ── Lists ── */
        ul {{ margin: 12px 0; padding-left: 25px; }}
        li {{ margin-bottom: 8px; line-height: 1.6; }}
        .logic-list {{ margin: 10px 0; padding-left: 0; list-style-type: none; }}
        .logic-item {{ margin-bottom: 8px; display: block; line-height: 1.5; }}

        /* ── Images ── */
        img {{ max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); margin: 20px 0; }}

        /* ── Footer ── */
        footer {{
            text-align: center;
            padding: 20px;
            font-size: 11px;
            color: #95a5a6;
            border-top: 1px solid #e0e0e0;
            margin-top: 40px;
        }}
    </style>
</head>
<body>

<div class="header-centered">
    <div class="logo">&lt;/&gt; Docs<span class="logo-accent">Gen</span></div>
    <div class="subtitle">Technical Intelligence Report</div>
    <div class="project-title">{safe_filename}</div>
    <div class="generation-date">Generated on: {generation_date}</div>
</div>

<div class="content">
    {diagram_html}
    {main_content_html}
    {code_section_html}
</div>

<footer>
    AutoTest &amp; DocGen — Technical Intelligence Unit &nbsp;|&nbsp; {generation_date}
</footer>

</body>
</html>"""

    def _export(self, formatted_output: str, data: dict) -> bytes:
        return formatted_output.encode('utf-8')

    # ── نفس دالة PDF بالضبط ──────────────────────────────────────────────────
    def _convert_text_to_enhanced_html(self, content):
        content = content.replace("\\'", "'").replace('\\"', '"')
        content = re.sub(r'^File[:\s]+.*?\n', '', content, flags=re.MULTILINE)
        content = content.replace('---', '')

        sections = re.split(r'(?=## Class:)', content)
        html_output = ""

        for section in sections:
            if not section.strip():
                continue

            is_class = '## Class:' in section
            if is_class:
                class_name_match = re.search(r'## Class:\s*([^\n\(\\:]+)', section)
                class_name = class_name_match.group(1).strip() if class_name_match else "Unknown Class"
                section = re.sub(
                    r'## Class:.*?\n',
                    f'<div class="class-card"><h2 class="class-header">Class: {class_name}</h2><div class="class-content-wrapper">',
                    section, count=1
                )
            else:
                section = re.sub(r'^##\s+(.+)$', r'<h2 class="high-level-section">\1</h2>', section, flags=re.MULTILINE)

            section = section.replace('### Function:', '### Method:')

            if '### ' in section:
                parts = re.split(r'(?=### )', section)
                header_part = parts[0]
                methods_combined = ""
                for i in range(1, len(parts)):
                    m_sec = parts[i]
                    def clean_method_header(match):
                        full_line = match.group(1).strip()
                        if "init" in full_line.lower() or "Constructor" in full_line:
                            display_label = "Constructor"
                        else:
                            display_label = "Method"
                        clean_name = full_line.replace("Method:", "").replace("Constructor:", "").replace("`", "").replace("*", "").strip()
                        return f'<div class="method-container"><h3 class="method-title">{display_label}: {clean_name}</h3><div class="method-description-area">'
                    m_sec = re.sub(r'###\s*(.*)', clean_method_header, m_sec, count=1)
                    methods_combined += m_sec + "</div></div>"
                section = header_part + methods_combined

            keys = ['Complexity Level','Security Note','Impact Analysis','Best Practices','Purpose',
                    'Patterns','Main Components','Purpose & Responsibility','Executive Summary',
                    'Relationships','Logic Flow','Parameters','Returns','Description',
                    'Key Capabilities','Error Handling','Attributes','Application Lifecycle',
                    'Dependencies','API Routes Overview']
            for key in keys:
                pattern = rf'(?:\d+\.\s*)?\*\*{re.escape(key)}:\*\*\s*(.*)'
                section = re.sub(
                    pattern,
                    lambda m, k=key: f'<div class="key-group"><span class="detail-key">{k}:</span><div class="key-content">{m.group(1).strip()}</div></div>',
                    section, flags=re.IGNORECASE
                )

            section = re.sub(
                r"Architectural Recommendations:\s*(.+?)(?=(?:<div|###|##|$))",
                r'<div class="recommendation-box"><strong>Architectural Recommendations:</strong><br>\1</div>',
                section, flags=re.DOTALL
            )

            section = re.sub(r'^\s*(?:\d+\.)?(\d+\.\d+\.\s*.*)$', r'<li class="logic-item">\1</li>', section, flags=re.MULTILINE)
            section = re.sub(r'^\s*(\d+\.\s*.*)$', lambda m: f'<li class="logic-item">{m.group(1).strip()}</li>' if '<div' not in m.group(0) else m.group(0), section, flags=re.MULTILINE)
            section = re.sub(r'^\s*(-\s+.*)$', lambda m: f'<li class="logic-item">{m.group(1).strip()}</li>', section, flags=re.MULTILINE)
            section = re.sub(r'((?:<li class="logic-item">.*?</li>\s*)+)', r'<ul class="logic-list">\1</ul>', section, flags=re.DOTALL)

            def apply_beauty(text):
                text = re.sub(r"['`]([^'`\n]+)['`]", r'<span class="inline-code">\1</span>', text)
                text = re.sub(r'\*\*([^*]+)\*\*', r'<span class="highlighted-text">\1</span>', text)
                return text

            parts = re.split(r'(<[^>]+>)', section)
            for j in range(len(parts)):
                if not parts[j].startswith('<'):
                    if j > 0 and ('class="method-title"' in parts[j-1] or 'class="class-header"' in parts[j-1]):
                        continue
                    parts[j] = apply_beauty(parts[j])
            section = "".join(parts).replace('**', '')

            if is_class:
                section += "</div></div>"

            html_output += section

        return html_output