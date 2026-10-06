from django.db import models

from academics.models import Result


class NotificationLog(models.Model):
    class Channel(models.TextChoices):
        SMS = 'sms', 'SMS'
        EMAIL = 'email', 'Email'

    class Status(models.TextChoices):
        SENT = 'sent', 'Sent'
        SIMULATED = 'simulated', 'Simulated'
        FAILED = 'failed', 'Failed'

    result = models.ForeignKey(Result, on_delete=models.CASCADE, related_name='notifications')
    channel = models.CharField(max_length=10, choices=Channel.choices)
    status = models.CharField(max_length=10, choices=Status.choices)
    detail = models.CharField(max_length=255, blank=True)
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-sent_at']

    def __str__(self):
        return f'{self.get_channel_display()} to {self.result.student} - {self.status}'
