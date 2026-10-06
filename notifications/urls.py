from django.urls import path

from .views import africastalking_delivery_report


app_name = 'notifications'

urlpatterns = [
    path(
        'africastalking/delivery-reports/',
        africastalking_delivery_report,
        name='africastalking_delivery_report',
    ),
]