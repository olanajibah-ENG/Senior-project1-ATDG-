import re
import logging
from datetime import datetime
from io import BytesIO
from core_ai.ai_engine.doc.doc_generator import DocumentationGenerator, WEASYPRINT_AVAILABLE, XHTML2PDF_AVAILABLE, REPORTLAB_AVAILABLE
from core_ai.mongo_utils import get_mongo_db
from bson import ObjectId

# Fix imports for PDF libraries
if WEASYPRINT_AVAILABLE:
    try:
        from weasyprint import HTML
    except ImportError:
        WEASYPRINT_AVAILABLE = False

if XHTML2PDF_AVAILABLE:
    try:
        from xhtml2pdf import pisa
    except ImportError:
        XHTML2PDF_AVAILABLE = False

if REPORTLAB_AVAILABLE:
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    except ImportError:
        REPORTLAB_AVAILABLE = False


logger = logging.getLogger(__name__)

class PDFGenerator(DocumentationGenerator):

    def _get_original_filename_from_analysis_id(self, analysis_id):
     db = None
     try:
        db = get_mongo_db()
        if not db: return None

        try:
            query_id = ObjectId(analysis_id) if ObjectId.is_valid(analysis_id) else analysis_id
        except Exception:
            return None

        result = db.analysis_results.find_one({"_id": query_id})
        
        code_file_id = result.get('code_file_id') if result else None
        
        if code_file_id:
            try:
                file_query_id = ObjectId(str(code_file_id)) if ObjectId.is_valid(str(code_file_id)) else code_file_id
                code_file = db.code_files.find_one({"_id": file_query_id})
                if code_file:
                    return code_file.get('filename')
            except Exception as e:
                logger.error(f"Error fetching code file: {e}")

        return None
     except Exception as e:
        logger.error(f"Error in database lookup: {e}")
        return None
    

    def _format_output(self, content, data):

        content_str = str(content) if content else ""
        image_url = data.get('image_url', '')
        analysis_id = data.get('analysis_id', 'unknown')

        filename = "Analysis Report"
        filename_match = re.search(r'File[:\s]+([^\s\n]+)', content_str)
        if filename_match:
            filename = filename_match.group(1).strip()
        else:
            db_filename = self._get_original_filename_from_analysis_id(analysis_id)
            if db_filename: filename = db_filename
        
        safe_filename = filename.replace('<', '&lt;').replace('>', '&gt;')

        generation_date = datetime.now().strftime("%Y-%m-%d %H:%M")
        main_content_html = self._convert_text_to_enhanced_html(content_str)
        
        full_html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Technical Analysis Report - {safe_filename}</title>
            <style>
                @page {{
                    size: A4;
                    margin: 2.5cm 2cm;
                    @bottom-right {{
                        content: "Page " counter(page) " of " counter(pages);
                        font-size: 9pt;
                        color: #95a5a6;
                        font-family: 'Helvetica', 'Arial', sans-serif;
                        border-top: 1px solid #e0e0e0;
                        padding-top: 8px;
                    }}
                    @bottom-left {{
                        content: "AutoTest & DocGen"; 
                        font-size: 9pt;
                        color: #95a5a6; 
                        font-family: 'Helvetica', 'Arial', sans-serif;
                        padding-left: 0.5cm; 
                        border-top: 1px solid #e0e0e0;
                        padding-top: 8px;
                    }}
                }}
                * {{
                    box-sizing: border-box;
                }}
                
                body {{
                    font-family: 'Segoe UI', 'Helvetica Neue', 'Arial', sans-serif;
                    color: #2d3436;
                    line-height: 1.6;
                    direction: ltr;
                    background: #ffffff;
                    margin: 0;
                    padding: 0;
                }}
                
                .header-centered {{
                    text-align: center;
                    width: 100%;
                    padding: 100px 0;
                    color: #2d3436;
                    box-shadow: 0 10px 20px rgba(0,0,0,0.1);
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                    align-items: center;
                    page-break-after: always;
                    background: #ffffff;
                    height: 100vh;
                }}
                
                .logo {{
                    color: #5a3d9a;
                    font-size: 48pt;
                    font-weight: 800;
                    margin-bottom: 20px;
                    letter-spacing: -1px;
                    text-shadow: 0 2px 4px rgba(0,0,0,0.2);
                    margin-top: 30%;
                }}
                
                .logo-accent {{
                    color: #8e44ad;
                    font-weight: 800;
                }}
                
                .project-title {{
                    font-size: 24pt;
                    color: #2d3436;
                    margin-top: 20px;
                    font-weight: 500;
                    letter-spacing: 0.5px;
                }}
                
                .subtitle {{
                    color:#636e72 ;
                    font-size: 9pt;
                    text-transform: uppercase;
                    letter-spacing: 2px;
                    font-weight: 300;
                }}
                
                .generation-date {{
                    font-size: 10pt;
                    color: #b2bec3;
                    margin-top: 12px;
                    font-weight: 300;
                }}
                
                /* Enhanced text formatting */
                p {{
                    margin-bottom: 14px;
                    text-align: justify;
                    word-wrap: break-word;
                }}
                
                h2, h3 {{
                    page-break-after: avoid;
                    page-break-inside: avoid;
                }}
                
                ul {{
                    margin: 12px 0;
                    padding-left: 25px;
                }}
                
                li {{
                    margin-bottom: 8px;
                    line-height: 1.6;
                }}

                /* Enhanced inline code */
                code {{
                    background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
                    color: #2c3e50;
                    padding: 3px 8px;
                    border-radius: 4px;
                    font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                    font-size: 90%;
                    font-weight: 500;
                    border: 1px solid #e1e8ed;
                    box-shadow: 0 1px 2px rgba(0,0,0,0.05);
                }}
                
                /* Enhanced class card */
                .class-card {{
                    background: transparent;
                    border: none;
                    padding: 0;
                    margin-top: 50px;
                    page-break-inside: avoid;
                    page-break-before: always;
                }}
                
                /* Enhanced class header */
                .class-header {{
                    background: linear-gradient(135deg, #4834d4 0%, #341f97 100%);
                    padding: 15px 25px;
                    display: inline-block;
                    border-radius: 0 10px 10px 0;
                    margin-top: 20px;
                    font-size: 22pt;
                    color: #ffffff;
                    font-weight: 600;
                    text-shadow: 0 1px 2px rgba(0,0,0,0.1);
                    box-shadow: 0 4px 15px rgba(72,52,212,0.3);
                }}

                .detail-key {{
                    color: #2980b9;
                    font-weight: 700;
                    text-transform: uppercase;
                    font-size: 10pt;
                    display: block;
                    margin-top: 15px;
                    margin-bottom: 5px;
                    margin-left: 1px; 
                    border-left: 3px solid #3498db;
                    padding: 2px 8px;
                    background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
                    border-radius: 0 6px 6px 0;
                    letter-spacing: 0.5px;
                    box-shadow: 0 2px 4px rgba(33, 150, 243, 0.1);
                    width: 100%;
                }}
                
                /* Enhanced highlighted text */
                .highlighted-text {{
                    color: #a29bfe;
                    font-weight: 600;
                    background: rgba(162, 155, 254, 0.1);
                    padding: 2px 6px;
                    border-radius: 4px;
                    font-size: 95%;
                }}
                
                /* Enhanced inline code */
                .inline-code {{
                    background: rgba(162, 155, 254, 0.15);
                    color: #6c5ce7;
                    padding: 2px 6px;
                    border-radius: 4px;
                    font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                    font-size: 90%;
                    font-weight: 500;
                    border: 1px solid rgba(162, 155, 254, 0.3);
                }}

                .source-code {{
                    background: #f8f9fa;
                    color: #2c3e50;
                    padding: 25px;
                    border-radius: 8px;
                    font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                    font-size: 9pt;
                    line-height: 1.6;
                    border: 1px solid #dee2e6;
                    white-space: pre-wrap;
                    word-wrap: break-word;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
                    position: relative;
                }}
                
                .source-code::before {{
                    content: "CODE";
                    position: absolute;
                    top: 8px;
                    right: 12px;
                    font-size: 7pt;
                    color: #6c757d;
                    font-weight: 600;
                    letter-spacing: 2px;
                }}

                /* Enhanced high level sections */
                .high-level-section {{
                    color: #2c3e50;
                    font-size: 22pt;
                    border-bottom: 3px solid #5a3d9a;
                    padding-bottom: 12px;
                    margin-top: 40px;
                    margin-bottom: 20px;
                    font-weight: 600;
                    position: relative;
                    padding-left: 15px;
                }}
                
                .high-level-section::before {{
                    content: "";
                    position: absolute;
                    left: 0;
                    top: 0;
                    bottom: 0;
                    width: 4px;
                    border-radius: 2px;
                    background: #5a3d9a;
                }}

                .method-title {{
                    color: #ffffff;
                    padding: 12px 20px;
                    font-size: 14pt;
                    margin: 0;
                    font-weight: 600;
                    background: linear-gradient(135deg, #6c5ce7 0%, #a29bfe 100%) !important;
                    border-radius: 8px 8px 0 0;
                }}

                .method-container {{
                    border: 1px solid #e8eaf6; 
                    border-left: 5px solid #6c5ce7; 
                    border-radius: 8px;
                    margin-top: 25px;
                    margin-bottom: 25px;
                    background: #fbfbff; 
                    page-break-inside: avoid;
                    box-shadow: 0 4px 10px rgba(108, 92, 231, 0.08); 
                    overflow: hidden;
                }}
                
                .method-description-area {{
                    padding:  20px;
                    background: transparent;
                    border: none;
                }}     

                .class-content-wrapper {{
                    margin-left: 30px;
                    padding-left: 25px;
                    margin-top: 15px;
                    position: relative;
                }}
                
                .logic-list {{
                  margin: 10px 0;
                  padding-left: 0; 
                  list-style-type: none; 
                }}

                .logic-item {{
                  margin-bottom: 8px;
                  display: block;
                  text-indent: 0; 
                  padding-left: 0;
                  line-height: 1.5;
                }}

                .key-group{{
                 margin-top: 15px;
                 margin-bottom: 10px;
                 display: block;
                }}

                .key-content {{
                  margin-left: 5px;
                  display: block;
                  text-align: left;
                }}
                
                .content {{
                    margin-top: 20px;
                    page-break-before: always;
                }}
                
                .code-section {{
                    margin-top: 40px;
                    page-break-before: always;
                }}
                
                .code-section h3 {{
                    color: #2c3e50;
                    font-size: 18pt;
                    margin-bottom: 15px;
                    font-weight: 600;
                }}
                
                .code-section h4 {{
                    color: #7f8c8d;
                    font-size: 12pt;
                    margin-bottom: 15px;
                    font-weight: 400;
                }}
                
                .code-note {{
                    font-size: 9pt;
                    color: #95a5a6;
                    font-style: italic;
                    margin-top: 10px;
                    text-align: center;
                }}
                
                img {{
                    max-width: 100%;
                    height: auto;
                    border-radius: 8px;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                    margin: 20px 0;
                }}
                
                .recommendation-box {{
                    background:  #f3f0ff;
                    border-left: 5px solid  #6c5ce7; 
                    padding: 15px;
                    margin-top: 20px;
                    border-radius: 0 10px 10px 0;
                    font-style: italic;
                    display:block;
                    color:  #4834d4;
                    box-shadow: 0 2px 8px rgba(108, 92, 231, 0.1);  
                }}
                
                /* PDF specific fixes */
                @media print {{
                    body {{
                        -webkit-print-color-adjust: exact;
                        print-color-adjust: exact;
                    }}
                    
                    .class-header {{
                        -webkit-print-color-adjust: exact;
                        print-color-adjust: exact;
                    }}
                    
                    .method-title {{
                        -webkit-print-color-adjust: exact;
                        print-color-adjust: exact;
                    }}
                    
                    .detail-key {{
                        -webkit-print-color-adjust: exact;
                        print-color-adjust: exact;
                    }}
                    
                    .highlighted-text {{
                        -webkit-print-color-adjust: exact;
                        print-color-adjust: exact;
                    }}
                    
                    .inline-code {{
                        -webkit-print-color-adjust: exact;
                        print-color-adjust: exact;
                    }}
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

            {f'<div style="text-align:center;margin-bottom: 20px;"><h3>Architecture Visualization</h3><img src="{image_url}" style="width:100%; border: 1px solid #ddd; border-radius: 10px;"></div>' if image_url else ''}

            <div class="content">
                {main_content_html}
            </div>

            {f'''
            <div class="code-section" style="page-break-before: always;">
                <h3>Source Code Analysis</h3>
                <h4>{safe_filename}</h4>
                <div class="code-content">
                    <pre class="source-code">{data.get('code_content', '').replace('<', '&lt;').replace('>', '&gt;')[:1000000]}</pre>
                </div>
                {f'<p class="code-note">Note: Showing first 1000000 characters of the source code.</p>' if len(data.get('code_content', '')) > 1000000 else ''}
            </div>
            ''' if data and data.get('code_content') else ''}
        </body>
        </html>
        """
        return full_html


    def _convert_text_to_enhanced_html(self, content):
        # 1. تنظيف أولي وحذف الرموز التي تعيق المعالجة
        content = content.replace("\\'", "'").replace('\\"', '"')
        content = re.sub(r'^File[:\s]+.*?\n', '', content, flags=re.MULTILINE)
        content = content.replace('---', '')
        
        # 2. تقسيم الكلاسات
        sections = re.split(r'(?=## Class:)', content)
        html_output = "" 

        for section in sections:
            if not section.strip(): continue

            # معالجة اسم الكلاس - تحسين النمط لضمان الالتقاط
            is_class = '## Class:' in section
            if is_class:
                # نلتقط ما بعد Class: وحتى نهاية السطر أو بداية قوس
                class_name_match = re.search(r'## Class:\s*([^\n\(\:]+)', section)
                class_name = class_name_match.group(1).strip() if class_name_match else "Unknown Class"
                section = re.sub(r'## Class:.*?\n', 
                               f'<div class="class-card"><h2 class="class-header">Class: {class_name}</h2><div class="class-content-wrapper">', 
                               section, count=1)
            else:
                section = re.sub(r'^##\s+(.+)$', r'<h2 class="high-level-section">\1</h2>', section, flags=re.MULTILINE)

            # 3. توحيد المسميات (إلغاء Function تماماً)
            # هذه الخطوة تتم قبل تقسيم الميثودات لضمان التوحيد
            section = section.replace('### Function:', '### Method:')
            section = section.replace('### Constructor:', '### Constructor:') # للتأكيد فقط

            # 4. معالجة الميثودات والكونستركتور
            if '### ' in section:
                parts = re.split(r'(?=### )', section)
                header_part = parts[0]
                methods_combined = ""
                
                for i in range(1, len(parts)):
                    m_sec = parts[i]
                    def clean_method_header(match):
                        full_line = match.group(1).strip()
                        # تحديد النوع بناءً على الاسم أو المحتوى
                        if "init" in full_line.lower() or "Constructor" in full_line:
                            display_label = "Constructor"
                        else:
                            display_label = "Method"
                        
                        # تنظيف الاسم من أي رموز ماركداون أو كلمات زائدة
                        clean_name = full_line.replace("Method:", "").replace("Constructor:", "").replace("`", "").replace("*", "").strip()
                        return f'<div class="method-container"><h3 class="method-title">{display_label}: {clean_name}</h3><div class="method-description-area">'

                    m_sec = re.sub(r'###\s*(.*)', clean_method_header, m_sec, count=1)
                    methods_combined += m_sec + "</div></div>"
                section = header_part + methods_combined

            # 5. معالجة المفاتيح (Keys) - تنفيذها قبل الترقيم لمنع التداخل
            keys = ['Complexity Level','Security Note','Impact Analysis','Best Practices','Purpose', 
                    'Patterns','Main Components','Purpose & Responsibility','Executive Summary',
                    'Relationships','Logic Flow','Parameters','Returns','Description',
                    'Key Capabilities','Error Handling', 'Attributes','Application Lifecycle','Dependencies','API Routes Overview']
            
            for key in keys:
                # نمط يلتقط المفتاح حتى لو سبقه أرقام (مثل 1. **Purpose**) ليقوم بتنظيفها
                pattern = rf'(?:\d+\.\s*)?\*\*{re.escape(key)}:\*\*\s*(.*)'
                section = re.sub(pattern, lambda m: f'<div class="key-group"><span class="detail-key">{key}:</span><div class="key-content">{m.group(1).strip()}</div></div>', section, flags=re.IGNORECASE)

            # 6. Architectural Recommendations
            section = re.sub(
                r"Architectural Recommendations:\s*(.+?)(?=(?:<div|###|##|$))", 
                r'<div class="recommendation-box"><strong>Architectural Recommendations:</strong><br>\1</div>', 
                section, flags=re.DOTALL
            )

            # 7. الترقيم والتعداد (Logic Flow) - تنظيف المسافات الزائدة
            # نلتقط الأرقام مثل 1.1 أو 1. ونحولها لـ li
            section = re.sub(r'^\s*(?:\d+\.)?(\d+\.\d+\.\s*.*)$', r'<li class="logic-item">\1</li>', section, flags=re.MULTILINE)
            section = re.sub(r'^\s*(\d+\.\s*.*)$', lambda m: f'<li class="logic-item">{m.group(1).strip()}</li>' if '<div' not in m.group(0) else m.group(0), section, flags=re.MULTILINE)
            section = re.sub(r'^\s*(-\s+.*)$', lambda m: f'<li class="logic-item">{m.group(1).strip()}</li>', section, flags=re.MULTILINE)
            
            # تجميع الـ li داخل ul
            section = re.sub(r'((?:<li class="logic-item">.*?</li>\s*)+)', r'<ul class="logic-list">\1</ul>', section, flags=re.DOTALL)

            # 8. التنسيقات الجمالية (Inline Code) مع حماية العناوين
            def apply_beauty(text):
                # تلوين ' ' و ` `
                text = re.sub(r"['`]([^'`\n]+)['`]", r'<span class="inline-code">\1</span>', text)
                # تلوين النصوص العريضة المتبقية (التي لم تتحول لمفاتيح)
                text = re.sub(r'\*\*([^*]+)\*\*', r'<span class="highlighted-text">\1</span>', text)
                return text

            parts = re.split(r'(<[^>]+>)', section)
            for j in range(len(parts)):
                # لا نطبق التنسيق الملون إذا كان النص داخل عنوان ميثود أو كلاس
                if not parts[j].startswith('<'):
                    if j > 0 and ('class="method-title"' in parts[j-1] or 'class="class-header"' in parts[j-1]):
                        continue 
                    parts[j] = apply_beauty(parts[j])
            
            section = "".join(parts).replace('**', '') # تنظيف نهائي

            if is_class:
                section += "</div></div>" 
            
            html_output += section

        return html_output

    def _export(self, formatted_output: str, data: dict) -> bytes:
        """
        Override the default _export method to convert HTML to PDF
        """
        return self._export_pdf(formatted_output)

    def _export_pdf(self, html_content: str) -> bytes:
        """
        تحويل الـ HTML المنسق إلى PDF باستخدام المكتبات المتوفرة
        مع تحسينات للـ CSS لضمان التوافق
        """
        # Prepare HTML for better PDF rendering
        html_content = self._prepare_html_for_pdf(html_content)
        return self._export_pdf_with_fallback(html_content)
    
    def _prepare_html_for_pdf(self, html_content: str) -> str:
        """
        تحضير الـ HTML للـ PDF مع تحسينات CSS
        """
        # Add proper DOCTYPE and meta tags
        if not html_content.strip().startswith('<!DOCTYPE'):
            html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Documentation Report</title>
</head>
{html_content[html_content.find('<body>'):] if '<body>' in html_content else html_content}"""
        
        return html_content
    
    def _export_pdf_with_fallback(self, html_content: str) -> bytes:
        """
        محاولة تصدير PDF مع المكتبات المختلفة
        """
        if WEASYPRINT_AVAILABLE:
            try:
                logger.info("Using WeasyPrint for PDF generation (CSS3 support)")
                html_doc = HTML(string=html_content, base_url='')

                buffer = BytesIO()
                html_doc.write_pdf(buffer)

                pdf_data = buffer.getvalue()
                buffer.close()

                if len(pdf_data) > 0:
                    logger.info(f"PDF generated successfully with WeasyPrint, size: {len(pdf_data)} bytes")
                    return pdf_data

            except Exception as e:
                logger.warning(f"WeasyPrint failed: {str(e)}")

        if XHTML2PDF_AVAILABLE:
            try:
                logger.info("Falling back to xhtml2pdf for PDF generation")
                buffer = BytesIO()
                pisa_status = pisa.CreatePDF(src=html_content, dest=buffer, encoding='utf-8')

                pdf_data = buffer.getvalue()
                buffer.close()

                # التحقق من وجود أخطاء في إنشاء PDF ووجود محتوى فعلي
                if pisa_status.err and len(pdf_data) == 0:
                    logger.warning(f"xhtml2pdf generated empty PDF with errors: {pisa_status.err}")
                    raise Exception(f"xhtml2pdf failed: {pisa_status.err}")
                
                if len(pdf_data) > 0:
                    if pisa_status.err:
                        logger.warning(f"xhtml2pdf generated PDF with warnings: {pisa_status.err}")
                    logger.info(f"PDF generated successfully with xhtml2pdf, size: {len(pdf_data)} bytes")
                    return pdf_data
                else:
                    logger.warning("xhtml2pdf generated empty PDF without errors")

            except Exception as e:
                logger.warning(f"xhtml2pdf failed: {str(e)}")

        if REPORTLAB_AVAILABLE:
            try:
                logger.info("Falling back to ReportLab for PDF generation")
                buffer = BytesIO()

                doc = SimpleDocTemplate(buffer, pagesize=letter)
                styles = getSampleStyleSheet()

                clean_text = re.sub(r'<[^>]+>', '', html_content)
                clean_text = re.sub(r'\n\s*\n', '\n\n', clean_text.strip())

                story = []
                for paragraph in clean_text.split('\n\n'):
                    if paragraph.strip():
                        p = Paragraph(paragraph.strip(), styles['Normal'])
                        story.append(p)
                        story.append(Spacer(1, 12))

                doc.build(story)
                pdf_data = buffer.getvalue()
                buffer.close()

                if len(pdf_data) > 0:
                    logger.info(f"PDF generated successfully with ReportLab, size: {len(pdf_data)} bytes")
                    return pdf_data

            except Exception as e:
                logger.warning(f"ReportLab failed: {str(e)}")

        raise ValueError("All PDF generation methods failed. Please check that at least one PDF library is properly installed.")