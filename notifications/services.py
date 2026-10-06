"""
Delivery logic for result alerts.

send_result_alert(result) is the single entry point: call it once a result
is approved. It sends an email (via Django's configured EMAIL_BACKEND) and
an SMS (via Africa's Talking), and writes one NotificationLog row per channel either
way, so the admin's notification log always reflects what really happened.

SMS falls back to a SIMULATED status when Africa's Talking credentials are not configured,
so the whole flow can be demonstrated without a paid SMS account. Swap in
an Africa's Talking API key and application username to switch on live delivery
-- no other code changes needed.
"""

import requests
from django.conf import settings
from django.core.mail import send_mail

from .models import NotificationLog


def _africas_talking_result(response):
    """Return the first provider recipient result and a compact detail string."""
    try:
        payload = response.json()
    except (ValueError, requests.exceptions.JSONDecodeError):
        return None, response.text[:220]

    sms_data = payload.get('SMSMessageData') or {}
    recipients = sms_data.get('Recipients') or []
    if not recipients:
        return None, sms_data.get('Message', response.text[:220])

    recipient = recipients[0]
    status = recipient.get('status', 'Unknown')
    message_id = recipient.get('messageId', '')
    cost = recipient.get('cost', '')
    detail = f'Provider status: {status}'
    if message_id:
        detail += f'; message ID: {message_id}'
    if cost:
        detail += f'; cost: {cost}'
    return status.lower(), detail[:255]


def _build_message(result):
    student_name = result.student.get_full_name() or result.student.username
    return (
        f'Hi {student_name}, your result for {result.course.course_code} '
        f'({result.semester} semester, {result.session}) is now available. '
        f'Score: {result.score} Grade: {result.grade}.'
    )


def _send_email(result, message):
    try:
        send_mail(
            subject=f'Result released: {result.course.course_code}',
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[result.student.email],
            fail_silently=False,
        )
        NotificationLog.objects.create(result=result, channel=NotificationLog.Channel.EMAIL,
                                        status=NotificationLog.Status.SENT,
                                        detail=f'Sent to {result.student.email}')
    except Exception as exc:  # noqa: BLE001 - log any backend failure, don't crash the request
        NotificationLog.objects.create(result=result, channel=NotificationLog.Channel.EMAIL,
                                        status=NotificationLog.Status.FAILED, detail=str(exc)[:255])


def _send_sms(result, message):
    phone = result.student.phone
    if not all((settings.AFRICASTALKING_USERNAME, settings.AFRICASTALKING_API_KEY)):
        NotificationLog.objects.create(
            result=result, channel=NotificationLog.Channel.SMS,
            status=NotificationLog.Status.SIMULATED,
            detail=f"Africa's Talking credentials not configured. Would send to {phone}: \"{message}\"",
        )
        return
    try:
        data = {
            'username': settings.AFRICASTALKING_USERNAME,
            'to': phone,
            'message': message,
        }
        if settings.AFRICASTALKING_SENDER_ID:
            data['from'] = settings.AFRICASTALKING_SENDER_ID
        response = requests.post(
            settings.AFRICASTALKING_SMS_URL,
            headers={
                'apiKey': settings.AFRICASTALKING_API_KEY,
                'Accept': 'application/json',
            },
            data=data,
            timeout=10,
        )
        provider_status, provider_detail = _africas_talking_result(response)
        if response.status_code in (200, 201) and provider_status in {
            'sent', 'submitted', 'buffered', 'success'
        }:
            NotificationLog.objects.create(result=result, channel=NotificationLog.Channel.SMS,
                                            status=NotificationLog.Status.SENT,
                                            detail=f'Sent to {phone}; {provider_detail}')
        else:
            NotificationLog.objects.create(result=result, channel=NotificationLog.Channel.SMS,
                                            status=NotificationLog.Status.FAILED,
                                            detail=f"Africa's Talking responded {response.status_code} for {phone}: {provider_detail}")
    except Exception as exc:  # noqa: BLE001
        NotificationLog.objects.create(result=result, channel=NotificationLog.Channel.SMS,
                                        status=NotificationLog.Status.FAILED, detail=str(exc)[:255])


def send_result_alert(result):
    """Send both channels for one approved result. Never raises."""
    message = _build_message(result)
    _send_email(result, message)
    _send_sms(result, message)