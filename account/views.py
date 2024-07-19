from django.shortcuts import render, redirect
from django.views import View
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.db.models import Q
import csv
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import transaction
from .models import Account
from .forms import UploadDataFileForm
from transaction.models import Transactions


class AccountListView(ListView):
    model = Account
    context_object_name = "accounts"
    template_name = "account/account_list.html"

    def get_queryset(self, *args, **kwargs):
        qs = super().get_queryset(*args, **kwargs)
        return qs.order_by("-id")


class AccountDetailsView(DetailView):
    model = Account
    context_object_name = "account"
    template_name = "account/account_details.html"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        account = self.get_object()

        transactions = Transactions.objects.filter(
            Q(sender=account) | Q(recipient=account)
        ).order_by("-id")
        context["transactions"] = transactions

        return context


class AccountDetailsView(DetailView):
    model = Account
    context_object_name = "account"
    template_name = "account/account_details.html"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        account = self.get_object()
        transactions = Transactions.objects.filter(
            Q(sender=account) | Q(recipient=account)
        ).order_by("-id")
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

            if not self._is_file_csv(csv_file):
                return self._render_form_with_errors(
                    request, form, "Uploaded file is not a CSV file."
                )

            try:
                accounts_to_create, accounts_to_update, skipped_rows = (
                    self._process_csv_file(csv_file)
                )

                if accounts_to_create or accounts_to_update:
                    self._save_accounts(accounts_to_create, accounts_to_update)
                    messages.success(request, "Accounts imported successfully.")
                if skipped_rows:
                    messages.warning(
                        request,
                        f"Some rows were skipped due to missing fields: {', '.join(map(str, skipped_rows))}.",
                    )
                    return render(request, self.template_name, {"form": form})
    
                return redirect("import-accounts")

            except ValidationError as e:
                error_message = (
                    " ".join(e.messages) if hasattr(e, "messages") else str(e)
                )
                messages.error(request, error_message)
            except Exception as e:
                messages.error(request, f"{e}")

        for field, errors in form.errors.items():
            for error in errors:
                messages.error(request, f"{error}")

        return render(request, self.template_name, {"form": form})

    def _process_csv_file(self, csv_file):
        accounts_to_create = []
        accounts_to_update = []
        skipped_rows = []

        try:
            decoded_file = csv_file.read().decode("utf-8").splitlines()
            reader = csv.DictReader(decoded_file)
            required_fields = ["ID", "Name", "Balance"]
            existing_accounts = {
                account.ref: account for account in Account.objects.all()
            }
            headers = reader.fieldnames
            if not headers:
                raise ValidationError("The CSV file does not contain any headers.")
            missing_headers = [
                field for field in required_fields if field not in headers
            ]
            if missing_headers:
                raise ValidationError(
                    f"Missing required headers in CSV: {', '.join(missing_headers)}"
                )
            rows = list(reader)
            if not rows:
                raise ValidationError(
                    "The CSV file contains only headers and no data rows."
                )

            for index, row in enumerate(rows):
                if not all(
                    field in row and row[field].strip() for field in required_fields
                ):
                    skipped_rows.append(index + 1)  # Row numbers are 1-based
                    continue

                account_ref = row["ID"]
                name = row["Name"]
                balance = self._parse_balance(row["Balance"])

                if account_ref in existing_accounts:
                    account = existing_accounts[account_ref]
                    account.name = name
                    account.balance = balance
                    accounts_to_update.append(account)
                else:
                    accounts_to_create.append(
                        Account(ref=account_ref, name=name, balance=balance)
                    )

        except csv.Error as e:
            raise Exception(f"Error reading CSV file: {e}")
        except ValidationError as e:
            raise Exception(f"{e.message}")

        return accounts_to_create, accounts_to_update, skipped_rows

    def _parse_balance(self, balance_str):
        try:
            balance = float(balance_str)
            if balance < 0:
                raise ValueError("Balance cannot be negative.")
            return balance
        except ValueError as e:
            raise ValueError(f"{e}")

    def _save_accounts(self, accounts_to_create, accounts_to_update):
        try:
            with transaction.atomic():
                Account.objects.bulk_create(accounts_to_create, batch_size=500)
                Account.objects.bulk_update(
                    accounts_to_update, ["name", "balance"], batch_size=500
                )
        except Exception as e:
            raise Exception(f"Error saving accounts: {e}")

    def _is_file_csv(self, file):
        return file.name.endswith(".csv")

    def _render_form_with_errors(self, request, form, error_message):
        messages.error(request, error_message)
        return render(request, self.template_name, {"form": form})
