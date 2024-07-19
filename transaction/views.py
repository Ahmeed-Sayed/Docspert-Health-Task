from django.shortcuts import redirect, render
from django.views import View
from django.contrib import messages

from .forms import TransactionForm
from .models import Transactions


class BalanceTransferView(View):

    def get(self, request):
        form = TransactionForm()

        return render(request, "transaction/balance_transaction.html", {"form": form})

    def post(self, request):

        form = TransactionForm(data=request.POST)

        if form.is_valid():

            try:
                cleaned_data = form.cleaned_data
                sender_ref, recpeient_ref, amount = (
                    cleaned_data.get("sender"),
                    cleaned_data.get("recepient"),
                    cleaned_data.get("amount"),
                )
                Transactions.transfer(
                    sender_ref=sender_ref,
                    transaction_amount=amount,
                    recipient_ref=recpeient_ref,
                )

                messages.success(request, "Transaction Completed Successfully")
            except Exception as e:
                messages.error(request, f"Error making transaction {e}")
        else:
            for field, error_list in form.errors.items():
                for error in error_list:
                    messages.error(request, f"{error}")

        return redirect("balance-transaction")
