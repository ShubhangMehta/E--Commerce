from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

def send_html_email(subject, to_email, template_name, context):
    """
    Sends an HTML email to the specified recipient.

    param subject: Subject of the email
    param to_email: Recipient's email address
    param template_name: Name of the HTML template to render
    param context: Context dictionary for rendering the template
    """
    # Render the HTML content using the provided template and context
    html_content = render_to_string(template_name, context)

    # Create the email message
    email = EmailMultiAlternatives(
        subject=subject,
        body='This is an HTML email. Please view it in an HTML-compatible email viewer.',
        to=[to_email]
    )

    # Attach the HTML content to the email
    email.attach_alternative(html_content, "text/html")

    # Send the email
    email.send()