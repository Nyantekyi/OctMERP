"""
apps/common/utils/pdf.py  — PDF generation helpers (WeasyPrint).
"""

import io
from django.template.loader import render_to_string

try:
    from weasyprint import HTML, CSS
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False


def render_to_pdf(template_name: str, context: dict, base_url: str = None) -> bytes:
    """
    Render a Django HTML template to a PDF bytestring.

    :param template_name: e.g. 'accounting/invoice_pdf.html'
    :param context: template context dict
    :param base_url: absolute URL used to resolve relative URLs in the template
    :returns: PDF bytes
    :raises RuntimeError: if WeasyPrint is not installed
    """
    if not WEASYPRINT_AVAILABLE:
        raise RuntimeError(
            "WeasyPrint is not installed. Add 'WeasyPrint' to your requirements."
        )
    html_string = render_to_string(template_name, context)
    html = HTML(string=html_string, base_url=base_url)
    return html.write_pdf()
