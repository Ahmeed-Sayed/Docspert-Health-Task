from django.test import TestCase
from django.urls import reverse
from django.contrib.messages import get_messages
from .models import Account

class BalanceTransferViewTests(TestCase):

    def setUp(self):
        self.url = reverse("balance-transaction")
        self.sender = Account.objects.create(ref="1", name="John", balance=1000.0)
        self.recipient = Account.objects.create(ref="2", name="Jane", balance=500.0)

    def post_data(self, data):
        response = self.client.post(self.url, data)
        return response

    def test_valid_transaction(self):
        data = {
            "sender": self.sender.ref,
            "recipient": self.recipient.ref,
            "amount": 100.0,
        }
        response = self.post_data(data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.url)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "Transaction Completed Successfully")
        self.sender.refresh_from_db()
        self.recipient.refresh_from_db()
        self.assertEqual(self.sender.balance, 900.0)
        self.assertEqual(self.recipient.balance, 600.0)

    def test_non_existent_sender_account(self):
        data = {"sender": "999", "recipient": self.recipient.ref, "amount": 100.0}
        response = self.post_data(data)
        self.assertEqual(response.status_code, 200)
        form = response.context["form"]
        self.assertTrue(form.errors)
        self.assertIn("Sender with reference '999' does not exist.", form.errors["sender"])
        
    def test_non_existent_recipient_account(self):
        data = {"sender": self.sender.ref, "recipient": "999", "amount": 100.0}
        response = self.post_data(data)
        self.assertEqual(response.status_code, 200)
        form = response.context["form"]
        self.assertTrue(form.errors)
        self.assertIn("Recipient with reference '999' does not exist.", form.errors["recipient"])

    def test_empty_account_reference(self):
        data = {"sender": "", "recipient": self.recipient.ref, "amount": 100.0}
        response = self.post_data(data)
        self.assertEqual(response.status_code, 200)
        form = response.context["form"]
        self.assertTrue(form.errors)
        self.assertIn("This field is required.", form.errors["sender"])

    def test_empty_amount(self):
        data = {
            "sender": self.sender.ref,
            "recipient": self.recipient.ref,
            "amount": "",
        }
        response = self.post_data(data)
        self.assertEqual(response.status_code, 200)
        form = response.context["form"]
        self.assertTrue(form.errors)
        self.assertIn("This field is required.", form.errors["amount"])

    def test_negative_amount(self):
        data = {
            "sender": self.sender.ref,
            "recipient": self.recipient.ref,
            "amount": -100.0,
        }
        response = self.post_data(data)
        self.assertEqual(response.status_code, 200)
        form = response.context["form"]
        self.assertTrue(form.errors)
        self.assertIn("Ensure this value is greater than or equal to 5.0.", form.errors["amount"])

    def test_amount_too_large(self):
        data = {
            "sender": self.sender.ref,
            "recipient": self.recipient.ref,
            "amount": 10000000000000000000.0,
        }
        response = self.post_data(data)
        self.assertEqual(response.status_code, 200)
        form = response.context["form"]
        self.assertTrue(form.errors)
        self.assertIn("Ensure that there are no more than 18 digits before the decimal point.", form.errors["amount"])

    def test_amount_greater_than_balance(self):
        data = {
            "sender": self.sender.ref,
            "recipient": self.recipient.ref,
            "amount": 2000.0,
        }
        response = self.post_data(data)
        self.assertEqual(response.status_code, 200)
        form = response.context["form"]
        self.assertTrue(form.non_field_errors())
        self.assertIn("Insufficient funds", form.non_field_errors()[0])
        self.sender.refresh_from_db()
        self.recipient.refresh_from_db()
        self.assertEqual(self.sender.balance, 1000.0)
        self.assertEqual(self.recipient.balance, 500.0)

    def test_sender_and_recipient_same(self):
        data = {
            "sender": self.sender.ref,
            "recipient": self.sender.ref,
            "amount": 100.0,
        }
        response = self.post_data(data)
        self.assertEqual(response.status_code, 200)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn("Sender and recipient cannot be the same.", str(messages[0]))
        self.sender.refresh_from_db()
        self.recipient.refresh_from_db()
        self.assertEqual(self.sender.balance, 1000.0)
        self.assertEqual(self.recipient.balance, 500.0)