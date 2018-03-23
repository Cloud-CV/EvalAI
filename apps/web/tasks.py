import json
import logging
import requests

from django.conf import settings
from django.core.mail import send_mail

from evalai.celery import app

from smtplib import SMTPException

logger = logging.getLogger(__name__)


@app.task
def notify_admin_on_receiving_contact_message(webhook_url, name, email, message):
	
	# Send slack notification
	webhook_url = webhook_url
	data = {'text': '{} with email: {} has sent a message: {}'.format(name, email, message)}
	header = {'Content-type': 'application/json'}
	try:
		response = requests.post(webhook_url, headers=header, data=json.dumps(data))
		logger.info("Notification successfully sent to slack!")
	except requests.exceptions.HTTPError as e:
		logger.info("There is an error in sending notification with error {}".format(e))

	# Send Email to CloudCV Admin
	from_email = settings.EMAIL_HOST_USER
	text = "wants to contact EvalAI admin"
	subject = "{} {}".format(name, text)
	message = message
	to_email = [settings.ADMIN_EMAIL]
	try:
		send_mail(subject, message, from_email, to_email)
		logger.info("Email successfully sent to CloudCV Admin!")
	except SMTPException as e:
		logger.info("There was an error in sending an email: {}".format(e))
