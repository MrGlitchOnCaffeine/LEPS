import logging
import traceback

import requests
from flask import render_template, url_for, current_app

logger = logging.getLogger(__name__)

BREVO_API_URL = 'https://api.brevo.com/v3/smtp/email'

# HTTPS on port 443 is not blocked on Render's free tier the way SMTP
# ports 25/465/587 are — confirmed directly against this deployment via
# /admin/diagnostics/email-test. A generous but bounded timeout is kept
# here as a safety net, not because we expect it to be hit.
_REQUEST_TIMEOUT_SECONDS = 10


def _send_via_brevo(to_email: str, subject: str, html_body: str) -> bool:
    """
    Sends a single HTML email via Brevo's transactional email API.
    Returns True on success, False on any failure.
    Never raises — all failures are logged and swallowed here so a broken
    email must never take down a request that already succeeded elsewhere.
    """
    api_key = current_app.config.get('BREVO_API_KEY')
    from_email = current_app.config.get('BREVO_FROM_EMAIL')

    if not api_key or not from_email:
        logger.error(
            'Brevo is not configured — BREVO_API_KEY or BREVO_FROM_EMAIL '
            'is missing. Email to %s was not sent.',
            to_email
        )
        return False

    payload = {
        'sender': {'name': 'LEPS', 'email': from_email},
        'to': [{'email': to_email}],
        'subject': subject,
        'htmlContent': html_body
    }

    try:
        response = requests.post(
            BREVO_API_URL,
            headers={
                'accept': 'application/json',
                'api-key': api_key,
                'content-type': 'application/json'
            },
            json=payload,
            timeout=_REQUEST_TIMEOUT_SECONDS
        )

        if response.status_code == 201:
            logger.info('Email sent via Brevo to %s: %s', to_email, subject)
            return True

        # Brevo returns a JSON error body on failure — log it in full so
        # the real cause (bad key, unverified sender, malformed payload)
        # is visible instead of a generic failure.
        logger.error(
            'Brevo returned %s for %s: %s',
            response.status_code, to_email, response.text
        )
        return False

    except requests.exceptions.Timeout:
        logger.error(
            'Brevo request to %s timed out after %ss',
            to_email, _REQUEST_TIMEOUT_SECONDS
        )
        return False

    except Exception:
        logger.error(
            'Unexpected error sending via Brevo to %s:\n%s',
            to_email, traceback.format_exc()
        )
        return False


def _render_and_send(template_name: str, subject: str, to_email: str,
                      context: dict, error_context: str) -> bool:
    """
    Renders an email template and sends it via Brevo. Shared by every
    public send_* function below since they all follow the same
    render-then-send shape and only differ in template, subject, and context.
    """
    try:
        html_body = render_template(template_name, **context)
        return _send_via_brevo(to_email, subject, html_body)
    except Exception:
        logger.error(
            'Failed to build %s for %s:\n%s',
            error_context, to_email, traceback.format_exc()
        )
        return False


def send_receipt_email(to_email: str, applicant_name: str, application) -> bool:
    """
    Sends a confirmation email after an application is submitted.
    Returns True on success, False on failure. Never raises.
    """
    tracking_url = url_for(
        'main.application_details',
        reference_id=application.reference_id,
        _external=True
    )

    return _render_and_send(
        template_name='emails/receipt_email.html',
        subject=f'Application Received - {application.reference_id}',
        to_email=to_email,
        context={
            'applicant_name': applicant_name,
            'application': application,
            'tracking_url': tracking_url
        },
        error_context=f'receipt email for {application.reference_id}'
    )


def send_decision_email(
    to_email: str,
    applicant_name: str,
    application,
    new_status: str,
    admin_comment: str = None,
) -> bool:
    """
    Sends a status decision email after an administrator updates an application.
    Returns True on success, False on failure. Never raises.
    """
    tracking_url = url_for(
        'main.application_details',
        reference_id=application.reference_id,
        _external=True
    )

    return _render_and_send(
        template_name='emails/decision_email.html',
        subject=f'Application Update - {application.reference_id}',
        to_email=to_email,
        context={
            'applicant_name': applicant_name,
            'application': application,
            'new_status': new_status,
            'admin_comment': admin_comment,
            'tracking_url': tracking_url
        },
        error_context=f'decision email for {application.reference_id}'
    )
