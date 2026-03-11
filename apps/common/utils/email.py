"""
apps/common/utils/email.py  — Email sending helpers.
"""

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings


def send_template_email(
    subject: str,
    recipient_list: list[str],
    template_txt: str,
    template_html: str | None,
    context: dict,
    from_email: str | None = None,
):
    """
    Send a transactional email using Django templates.

    :param subject: Email subject
    :param recipient_list: List of recipient email addresses
    :param template_txt: Path to plain-text template
    :param template_html: Path to HTML template (optional)
    :param context: Template context dict
    :param from_email: Sender address (defaults to DEFAULT_FROM_EMAIL)
    """
    from_email = from_email or getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@erp.app")
    body = render_to_string(template_txt, context)
    msg = EmailMultiAlternatives(subject, body, from_email, recipient_list)
    if template_html:
        html_body = render_to_string(template_html, context)
        msg.attach_alternative(html_body, "text/html")
    msg.send()
