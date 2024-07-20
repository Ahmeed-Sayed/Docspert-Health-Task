from django.shortcuts import redirect, render
from django.views import View
from django.contrib import messages
from django.core.exceptions import ValidationError

from .forms import TransactionForm
from .models import Transactions


class BalanceTransferView(View):

    def get(self, request):
        form = TransactionForm()
        return render(request, "transaction/balance_transaction.html", {"form": form})

    def post(self, request):
        form = TransactionForm(data=request.POST)

        if form.is_valid():
            cleaned_data = form.cleaned_data
            sender_ref, recipient_ref, amount = (
                cleaned_data.get("sender"),
                cleaned_data.get("recepient"),
                cleaned_data.get("amount"),
            )
            if sender_ref == recipient_ref:
                messages.error(request, "Sender and recipient cannot be the same.")
            else:
                try:
                    Transactions.transfer(
                        sender_ref=sender_ref,
                        transaction_amount=amount,
                        recipient_ref=recipient_ref,
                    )
                    messages.success(request, "Transaction Completed Successfully")
                    return redirect("balance-transaction")
                except ValidationError as e:
                       messages.error(request, f"{e.message}")

                except Exception as e:
                    messages.error(request, f"Error making transaction: {e}")

        return render(request, "transaction/balance_transaction.html", {"form": form})
