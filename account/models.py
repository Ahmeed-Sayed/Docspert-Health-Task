from django.db import models


class Account(models.Model):

    ref = models.CharField(max_length=100, unique=True, null=False, blank=False)
    name = models.CharField(max_length=100, null=False, blank=False)
    balance = models.DecimalField(max_digits=100, decimal_places=2, default=0.00)

    def can_transfer(self, transaction_amount):
        return self.balance >= transaction_amount

    
    @classmethod
    def _get_account_by_ref(cls, ref):
        try:
            account = cls.objects.get(ref=ref)
            return account
        except cls.DoesNotExist:
            return None

    def __str__(self):
        return f"{self.ref } - {self.name} - {self.balance}"