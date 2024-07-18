from django.core.exceptions import ValidationError
from account.models import Account

def check_sender_exists(sender_ref):
    try:
        Account.objects.get(ref=sender_ref)
    except Account.DoesNotExist:
        raise ValidationError(f"Sender with reference '{sender_ref}' does not exist.")

def check_recipient_exists(recipient_ref):
    try:
        Account.objects.get(ref=recipient_ref)
    except Account.DoesNotExist:
        raise ValidationError(f"Recipient with reference '{recipient_ref}' does not exist.")