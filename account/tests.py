from django.test import TestCase
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import Account
from transaction.models import Transactions


class AccountListViewTests(TestCase):
    def setUp(self):
        self.account1 = Account.objects.create(ref="1", name="Account 1", balance=100.0)
        self.account2 = Account.objects.create(ref="2", name="Account 2", balance=200.0)

    def format_account(self, account):
        return f"{account.ref} : {account.name} : {account.balance:.2f}"

    def test_account_list_view_status_code(self):
        response = self.client.get(reverse("account-list"))
        self.assertEqual(response.status_code, 200)

    def test_account_list_view_template(self):
        response = self.client.get(reverse("account-list"))
        self.assertTemplateUsed(response, "account/account_list.html")

    def test_account_list_view_context(self):
        response = self.client.get(reverse("account-list"))
        self.assertTrue("accounts" in response.context)
        self.assertEqual(len(response.context["accounts"]), 2)
        self.assertQuerysetEqual(
            response.context["accounts"],
            [self.format_account(self.account2), self.format_account(self.account1)],
            transform=self.format_account,
            ordered=True,
        )


class AccountDetailsViewTests(TestCase):
    def setUp(self):
        self.account = Account.objects.create(ref="1", name="Account 1", balance=100.0)
        self.other_account = Account.objects.create(
            ref="2", name="Account 2", balance=200.0
        )
        self.transaction1 = Transactions.objects.create(
            sender=self.account, recipient=self.other_account, amount=50.0
        )
        self.transaction2 = Transactions.objects.create(
            sender=self.other_account, recipient=self.account, amount=75.0
        )

    def format_transaction(self, transaction):
        return f"{transaction.sender.ref} ---> {transaction.recipient.ref} : {transaction.amount:.2f}"

    def test_account_details_view_status_code(self):
        response = self.client.get(reverse("account-details", args=[self.account.pk]))
        self.assertEqual(response.status_code, 200)

    def test_account_details_view_template(self):
        response = self.client.get(reverse("account-details", args=[self.account.pk]))
        self.assertTemplateUsed(response, "account/account_details.html")

    def test_account_details_view_context(self):
        response = self.client.get(reverse("account-details", args=[self.account.pk]))
        self.assertTrue("account" in response.context)
        self.assertTrue("transactions" in response.context)
        self.assertEqual(response.context["account"], self.account)
        self.assertQuerysetEqual(
            response.context["transactions"],
            [
                self.format_transaction(self.transaction2),
                self.format_transaction(self.transaction1),
            ],
            transform=self.format_transaction,
            ordered=True,
        )


class ImportAccountsViewTests(TestCase):
    def setUp(self):
        self.url = reverse("import-accounts")

    def test_import_empty_file(self):
        empty_file = SimpleUploadedFile("empty.csv", b"")
        response = self.client.post(self.url, {"data_file": empty_file})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "The submitted file is empty.")

    def test_import_valid_csv(self):
        valid_csv = SimpleUploadedFile(
            "valid.csv", b"ID,Name,Balance\n1,John,100.0\n2,Jane,200.0"
        )
        response = self.client.post(self.url, {"data_file": valid_csv})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.url)
        self.assertEqual(Account.objects.count(), 2)

    def test_import_header_only_csv(self):
        header_only_csv = SimpleUploadedFile("header_only.csv", b"ID,Name,Balance\n")
        response = self.client.post(self.url, {"data_file": header_only_csv})
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response, "The CSV file contains only headers and no data rows."
        )

    def test_import_header_only_csv_with_extra_newline(self):
        header_only_csv = SimpleUploadedFile(
            "header_only_extra_newline.csv", b"ID,Name,Balance\n\n"
        )
        response = self.client.post(self.url, {"data_file": header_only_csv})
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response, "The CSV file contains only headers and no data rows."
        )

    def test_import_negative_balance(self):
        negative_balance_csv = SimpleUploadedFile(
            "negative_balance.csv", b"ID,Name,Balance\n1,John,-100.0\n"
        )
        response = self.client.post(self.url, {"data_file": negative_balance_csv})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Balance cannot be negative.")

    def test_import_missing_id_header(self):
        missing_id_header_csv = SimpleUploadedFile(
            "missing_id_header.csv", b"Name,Balance\nJohn,100.0\nJane,200.0"
        )
        response = self.client.post(self.url, {"data_file": missing_id_header_csv})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Missing required headers in CSV: ID")

    def test_import_missing_name_header(self):
        missing_name_header_csv = SimpleUploadedFile(
            "missing_name_header.csv", b"ID,Balance\n1,100.0\n2,200.0"
        )
        response = self.client.post(self.url, {"data_file": missing_name_header_csv})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Missing required headers in CSV: Name")

    def test_import_missing_balance_header(self):
        missing_balance_header_csv = SimpleUploadedFile(
            "missing_balance_header.csv", b"ID,Name\n1,John\n2,Jane"
        )
        response = self.client.post(self.url, {"data_file": missing_balance_header_csv})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Missing required headers in CSV: Balance")

    def test_import_missing_id_field(self):
        missing_id_csv = SimpleUploadedFile(
            "missing_id.csv", b"ID,Name,Balance\n,John,100.0\n2,Jane,200.0"
        )
        response = self.client.post(self.url, {"data_file": missing_id_csv})
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response, "Some rows were skipped due to missing fields: 1."
        )
        self.assertEqual(Account.objects.count(), 1)

    def test_import_missing_name_field(self):
        missing_name_csv = SimpleUploadedFile(
            "missing_name.csv", b"ID,Name,Balance\n1,,100.0\n2,Jane,200.0"
        )
        response = self.client.post(self.url, {"data_file": missing_name_csv})
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response, "Some rows were skipped due to missing fields: 1."
        )
        self.assertEqual(Account.objects.count(), 1)

    def test_import_missing_balance_field(self):
        missing_balance_csv = SimpleUploadedFile(
            "missing_balance.csv", b"ID,Name,Balance\n1,John,\n2,Jane,200.0"
        )
        response = self.client.post(self.url, {"data_file": missing_balance_csv})
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response, "Some rows were skipped due to missing fields: 1."
        )
        self.assertEqual(Account.objects.count(), 1)

    def test_import_multiple_missing_fields(self):
        multiple_missing_fields_csv = SimpleUploadedFile(
            "multiple_missing_fields.csv", b"ID,Name,Balance\n,John,\n2,Jane,200.0"
        )
        response = self.client.post(
            self.url, {"data_file": multiple_missing_fields_csv}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response, "Some rows were skipped due to missing fields: 1."
        )
        self.assertEqual(Account.objects.count(), 1)
