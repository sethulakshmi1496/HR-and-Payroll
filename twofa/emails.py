"""HTML email helper. Renders a Django template + sends via Django's
EmailMultiAlternatives. In dev (DEBUG=True), the console backend prints
both plain-text and html parts."""
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags


def send_html_mail(subject, template_name, context, to, from_email=None, attachments=None):
    """
    template_name: template path under /app/templates (e.g. "email/leave_request.html")
    context:       dict passed to the template
    to:            list of recipient emails
    """
    from_email = from_email or 'AEC HR <no-reply@aecgroup.in>'
    html_body = render_to_string(template_name, context)
    text_body = strip_tags(html_body)
    msg = EmailMultiAlternatives(str(subject), text_body, from_email, to)
    msg.attach_alternative(html_body, "text/html")
    for fname, content, mime in (attachments or []):
        msg.attach(fname, content, mime)
    msg.send(fail_silently=True)
    return True
