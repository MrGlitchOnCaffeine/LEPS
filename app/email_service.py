from flask import render_template, url_for
from flask_mail import Message
from app import mail


def send_receipt_email(to_email: str, applicant_name: str, application):
    """
    Sends a confirmation email immediately after an application is submitted.

    Parameters:
        to_email       - the applicant's registered email address
        applicant_name - the applicant's full name
        application    - the LoanApplication database record
    """
    subject = f'Application Received - {application.reference_id}'

    tracking_url = url_for(
        'main.application_details',
        reference_id=application.reference_id,
        _external=True
    )

    msg = Message(subject=subject, recipients=[to_email])
    msg.html = render_template(
        'emails/receipt_email.html',
        applicant_name=applicant_name,
        application=application,
        tracking_url=tracking_url
    )

    try:
        mail.send(msg)
        return True
    except Exception:
        return False


def send_decision_email(
    to_email: str,
    applicant_name: str,
    application,
    new_status: str,
    admin_comment: str = None
):
    """
    Sends a status decision email after an administrator updates an application.

    Parameters:
        to_email       - the applicant's registered email address
        applicant_name - the applicant's full name
        application    - the LoanApplication database record
        new_status     - the new status set by the administrator
        admin_comment  - optional administrator comment to include in the email
    """
    subject = f'Application Update - {application.reference_id}'

    tracking_url = url_for(
        'main.application_details',
        reference_id=application.reference_id,
        _external=True
    )

    msg = Message(subject=subject, recipients=[to_email])
    msg.html = render_template(
        'emails/decision_email.html',
        applicant_name=applicant_name,
        application=application,
        new_status=new_status,
        admin_comment=admin_comment,
        tracking_url=tracking_url
    )

    try:
        mail.send(msg)
        return True
    except Exception:
        return False


def send_result_email(to_email: str, applicant_name: str, application, prediction):
    """
    Sends the ML eligibility result email to the applicant.
    Retained for backwards compatibility but not used in the primary flow.

    Parameters:
        to_email       - the applicant's registered email address
        applicant_name - the applicant's full name
        application    - the LoanApplication database record
        prediction     - the Prediction database record
    """
    subject = f'Your Loan Eligibility Result - {application.reference_id}'

    msg = Message(subject=subject, recipients=[to_email])
    msg.html = render_template(
        'emails/result_email.html',
        applicant_name=applicant_name,
        application=application,
        prediction=prediction
    )

    try:
        mail.send(msg)
        return True
    except Exception:
        return False
