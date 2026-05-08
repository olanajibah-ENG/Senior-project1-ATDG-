from abc import ABC, abstractmethod
from io import BytesIO
import re
import logging

WEASYPRINT_AVAILABLE = False
XHTML2PDF_AVAILABLE = False
REPORTLAB_AVAILABLE = False

# Enable WeasyPrint for better PDF generation
try:
    from weasyprint import HTML, CSS
    WEASYPRINT_AVAILABLE = True
    print("WeasyPrint is available - using for high-quality PDF generation")
except ImportError as e:
    print(f"WeasyPrint not available: {e}")
    pass

try:
    from xhtml2pdf import pisa
    XHTML2PDF_AVAILABLE = True
except ImportError:
    pass

try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    REPORTLAB_AVAILABLE = True
except ImportError:
    pass

logger = logging.getLogger(__name__)

class DocumentationGenerator(ABC):
    """
    المحرك الأساسي لتوليد المستندات.
    Template Method Pattern: يحدد الهيكل العام لعملية التوليد
    ويسمح للفئات الفرعية بتخصيص الخطوات الفردية.
    """
    def generate(self, data: dict) -> bytes:
        """
        Template Method - يحدد الهيكل العام لعملية التوليد:
        1. استخراج المحتوى من البيانات
        2. تنسيق المحتوى (يتم تخصيصه في الفئات الفرعية)
        3. تصدير المحتوى (يتم تخصيصه في الفئات الفرعية)
        """
        try:
            content = data.get('content', '') if data else ''

            if content is None:
                content = ''
            elif not isinstance(content, str):
                logger.warning(f"Converting non-string content to string: {type(content)}")
                content = str(content)

            # Hook 1: تنسيق المحتوى (يتم تخصيصه في الفئات الفرعية)
            formatted_output = self._format_output(content, data)

            # Hook 2: تصدير المحتوى (يتم تخصيصه في الفئات الفرعية)
            return self._export(formatted_output, data)
        except Exception as e:
            logger.error(f"Error in generation: {str(e)}")
            raise

    @abstractmethod
    def _format_output(self, content: str, data: dict) -> str:
        """
        Hook Method - يجب على الفئات الفرعية تطبيقه لتخصيص تنسيق المحتوى.
        """
        pass

    def _export(self, formatted_output: str, data: dict) -> bytes:
        """
        Hook Method - يمكن للفئات الفرعية تخصيصه.
        القيمة الافتراضية: تصدير كـ UTF-8 bytes.
        """
        return formatted_output.encode('utf-8')

    def _export_pdf(self, html_content: str) -> bytes:
        """تحويل الـ HTML بالكامل إلى PDF مع دعم التنسيقات الفخمة"""

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

    def _prepare_for_rendering(self, html_content: str) -> str:
        """
        Helper Method - تجهيز الـ HTML لضمان أفضل نتيجة مع محركات PDF.
        يمكن استخدامه من قبل الفئات الفرعية عند الحاجة.
        """
        html_content = re.sub(r'<table', '<table style="width: 100%; table-layout: fixed;"', html_content)
        html_content = re.sub(r'<td>', '<td style="word-wrap: break-word; overflow: hidden;">', html_content)
        
        html_content = html_content.replace('<br>', '<br/>').replace('<hr>', '<hr/>')
        
        return html_content

    


    def _process_markdown_to_html(self, content: str) -> str:
        """
        دالة مساعدة لتحويل الـ Markdown الخام إلى HTML بسيط 
        يمكن استخدامها داخل _format_output في الملفات الفرعية.
        """
        content = self._process_code_blocks(content)
        
        content = self._process_markdown_tables(content)
        
        content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', content)
        content = re.sub(r'`(.*?)`', r'<code>\1</code>', content)
        
        return content
    
    def _process_code_blocks(self, content: str) -> str:
        code_pattern = r'```(?:[\w]*\n)?(.*?)```'
        def repl(m):
            code = m.group(1).replace('<', '&lt;').replace('>', '&gt;')
            return f'<div class="code-block"><pre>{code}</pre></div>'
        return re.sub(code_pattern, repl, content, flags=re.DOTALL)

    def _process_markdown_tables(self, content: str) -> str:
        table_pattern = r'(\|[^\n]+\|\n\|[-\s|:]+\|\n(?:\|[^\n]+\|\n?)*)'
        def table_repl(match):
            rows = match.group(1).strip().split('\n')
            html = ['<table>']
            for i, row in enumerate(rows):
                if i == 1: continue # سطر الفواصل
                tag = 'th' if i == 0 else 'td'
                cells = [c.strip() for c in row.split('|')[1:-1]]
                html.append(f'<tr>' + ''.join(f'<{tag}>{c}</{tag}>' for c in cells) + '</tr>')
            html.append('</table>')
            return '\n'.join(html)
        return re.sub(table_pattern, table_repl, content)