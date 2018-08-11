
from django.dispatch import Signal

bounce_received = Signal(providing_args=["mail_obj", "bounce_obj", "raw_message"])

complaint_received = Signal(providing_args=["mail_obj", "complaint_obj", "raw_message"])

delivery_received = Signal(providing_args=["mail_obj", "delivery_obj", "raw_message"])
