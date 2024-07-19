from django.db import models
from decimal import Decimal
from django.db import models, transaction

from account.models import Account
from django.core.exceptions import ValidationError

from django.utils import timezone


class Transactions(models.Model):
    sender = models.ForeignKey(
        Account, related_name="sent_transactions", on_delete=models.CASCADE
    )
    recipient = models.ForeignKey(
        Account, related_name="received_transactions", on_delete=models.CASCADE
    )
    amount = models.DecimalField(max_digits=100, decimal_places=2)
    created = models.DateTimeField(default=timezone.now)

    @classmethod
    def transfer(cls, sender_ref, transaction_amount, recipient_ref):

        transaction_amount = Decimal(str(transaction_amount))
        sender = Account._get_account_by_ref(sender_ref)
        recepient = Account._get_account_by_ref(recipient_ref)

        if sender.can_transfer(transaction_amount):

            with transaction.atomic():
                sender.balance -= transaction_amount
                recepient.balance += transaction_amount
                sender.save()
                recepient.save()

                cls.objects.create(
                    sender=sender,
                    recipient=recepient,
                    amount=transaction_amount,
                )
        else:
            raise ValidationError("Insufficient funds.")

    def __str__(self):
        return f"{self.sender.ref} ---> {self.recipient.ref} : {self.amount} "
