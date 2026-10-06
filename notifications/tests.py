from unittest.mock import Mock, patch

from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from academics.models import Course, Result

from .models import NotificationLog
from .services import _send_sms


class SmsDeliveryTests(TestCase):
	def setUp(self):
		self.student = User.objects.create_user(
			username='CSC/2021/001', password='pw', email='student@example.com',
			phone='+2348022222222', role=User.Role.STUDENT,
		)
		course = Course.objects.create(course_code='CSC301', title='Operating Systems')
		self.result = Result.objects.create(
			student=self.student, course=course, score=75,
			semester='first', session='2025/2026',
		)

	@patch('notifications.services.requests.post')
	def test_sends_africas_talking_request(self, post):
		post.return_value = Mock(
			status_code=201,
			text='{"SMSMessageData": {"Message": "Sent"}}',
			json=lambda: {
				'SMSMessageData': {
					'Recipients': [{'status': 'Sent', 'messageId': 'AT-123', 'cost': 'NGN 4.00'}],
				}
			},
		)

		with self.settings(
			AFRICASTALKING_USERNAME='sandbox',
			AFRICASTALKING_API_KEY='test-api-key',
			AFRICASTALKING_SENDER_ID='AFUSTA',
			AFRICASTALKING_SMS_URL='https://api.sandbox.africastalking.com/version1/messaging',
		):
			_send_sms(self.result, 'Your result is ready.')

		post.assert_called_once_with(
			'https://api.sandbox.africastalking.com/version1/messaging',
			headers={'apiKey': 'test-api-key', 'Accept': 'application/json'},
			data={
				'username': 'sandbox',
				'to': '+2348022222222',
				'message': 'Your result is ready.',
				'from': 'AFUSTA',
			},
			timeout=10,
		)
		log = NotificationLog.objects.get(channel=NotificationLog.Channel.SMS)
		self.assertEqual(log.status, NotificationLog.Status.SENT)
		self.assertIn('AT-123', log.detail)

	@patch('notifications.services.requests.post')
	def test_provider_failure_is_not_logged_as_sent(self, post):
		post.return_value = Mock(
			status_code=201,
			text='{"SMSMessageData": {"Message": "Sent"}}',
			json=lambda: {
				'SMSMessageData': {
					'Recipients': [{'status': 'Failed', 'messageId': 'AT-456'}],
				}
			},
		)

		with self.settings(
			AFRICASTALKING_USERNAME='yasira',
			AFRICASTALKING_API_KEY='test-api-key',
		):
			_send_sms(self.result, 'Your result is ready.')

		log = NotificationLog.objects.get(channel=NotificationLog.Channel.SMS)
		self.assertEqual(log.status, NotificationLog.Status.FAILED)
		self.assertIn('Failed', log.detail)

	def test_delivery_report_updates_matching_sms_log(self):
		log = NotificationLog.objects.create(
			result=self.result,
			channel=NotificationLog.Channel.SMS,
			status=NotificationLog.Status.SENT,
			detail='Sent to +2348022222222; Provider status: Sent; message ID: AT-789',
		)

		response = self.client.post(reverse('notifications:africastalking_delivery_report'), {
			'id': 'AT-789',
			'status': 'Failed',
			'phoneNumber': '+2348022222222',
			'failureReason': 'DeliveryFailure',
		})

		self.assertEqual(response.status_code, 200)
		log.refresh_from_db()
		self.assertEqual(log.status, NotificationLog.Status.FAILED)
		self.assertIn('DeliveryFailure', log.detail)
