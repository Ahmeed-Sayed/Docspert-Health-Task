from django.shortcuts import render, redirect
from django.views import View
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.db.models import Q
import csv
from django.contrib import messages

from django.db import transaction
from .models import Account
from .forms import UploadDataFileForm
from transaction.models import Transactions


class AccountListView(ListView):

    model = Account
    context_object_name = "accounts"
    template_name = "account/account_list.html"

    def get_queryset(self, *args, **kwargs):
        qs = super(AccountListView, self).get_queryset(*args, **kwargs)
        qs = qs.order_by("-id")
        return qs


class AccountDetailsView(DetailView):

    model = Account
    context_object_name = "account"
    template_name = "account/account_details.html"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        account = self.get_object()

        transactions = Transactions.objects.filter(
            Q(sender=account) | Q(recipient=account)
        ).order_by("created_at")
        context["transactions"] = transactions

        return context


class ImportAccountsView(View):
    form_class = UploadDataFileForm
    template_name = "account/import_accounts.html"

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, {"form": form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES["data_file"]
            try:
                accounts_to_create, accounts_to_update = self.process_csv_file(csv_file)
                self.save_accounts(accounts_to_create, accounts_to_update)
                messages.success(request, "Accounts imported successfully")
            except Exception as e:
                messages.error(request, f"Error importing accounts: {e}")

            return redirect("import-accounts")
        return render(request, self.template_name, {"form": form})

    @staticmethod
    def process_csv_file(csv_file):
        accounts_to_create = []
        accounts_to_update = []
        try:
            decoded_file = csv_file.read().decode("utf-8").splitlines()
            reader = csv.DictReader(decoded_file)
            existing_accounts = {
                account.ref: account for account in Account.objects.all()
            }

            for row in reader:
                account_ref = row["ID"]
                if account_ref in existing_accounts:
                    account = existing_accounts[account_ref]
                    account.name = row["Name"]
                    account.balance = row["Balance"]
                    accounts_to_update.append(account)
                else:
                    accounts_to_create.append(
                        Account(
                            ref=account_ref, name=row["Name"], balance=row["Balance"]
                        )
                    )
        except csv.Error as e:
            raise Exception(f"Error reading CSV file: {e}")
        except KeyError as e:
            raise Exception(f"Missing required field in CSV: {e}")
        except Exception as e:
            raise Exception(f"Unexpected error: {e}")

        return accounts_to_create, accounts_to_update

    @staticmethod
    def save_accounts(accounts_to_create, accounts_to_update):
        try:
            with transaction.atomic():
                Account.objects.bulk_create(accounts_to_create, batch_size=500)
                Account.objects.bulk_update(
                    accounts_to_update, ["name", "balance"], batch_size=500
                )
        except Exception as e:
            raise Exception(f"Error saving accounts: {e}")
