from django import forms

from .validators import check_recipient_exists, check_sender_exists


class TransactionForm(forms.Form):
    sender = forms.CharField(
        required=True, help_text="Sender ID", validators=[check_sender_exists]
    )
    recepient = forms.CharField(
        required=True, help_text="Recepient ID", validators=[check_recipient_exists]
    )
    amount = forms.DecimalField(
        decimal_places=2,
        min_value=5.00,
        initial=5.00,
        required=True,
        max_digits=20,
    )
