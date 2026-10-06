from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from .models import NotificationLog


@csrf_exempt
def africastalking_delivery_report(request):
    if request.method != 'POST':
        return HttpResponse(status=405)

    message_id = request.POST.get('id', '').strip()
    status = request.POST.get('status', '').strip()
    phone_number = request.POST.get('phoneNumber', '').strip()
    failure_reason = request.POST.get('failureReason', '').strip()

    if not message_id or not status:
        return HttpResponse(status=400)

    logs = NotificationLog.objects.filter(
        channel=NotificationLog.Channel.SMS,
        detail__contains=f'message ID: {message_id}',
    )
    log = logs.order_by('-sent_at').first()
    if log is not None:
        detail = f'Provider delivery status: {status}'
        if phone_number:
            detail += f' to {phone_number}'
        if failure_reason:
            detail += f'; reason: {failure_reason}'
        log.status = (
            NotificationLog.Status.SENT
            if status.lower() in {'success', 'sent'}
            else NotificationLog.Status.FAILED
        )
        log.detail = detail[:255]
        log.save(update_fields=['status', 'detail'])

    return HttpResponse(status=200)