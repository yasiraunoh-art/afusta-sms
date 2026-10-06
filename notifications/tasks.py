from celery import shared_task

from academics.models import Result

from .services import send_result_alert


@shared_task
def send_result_alert_task(result_id):
    """Celery entry point. Queued by academics.views when a result is approved."""
    result = Result.objects.select_related('student', 'course').get(pk=result_id)
    send_result_alert(result)
