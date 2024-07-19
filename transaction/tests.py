from django.urls import reverse
from django.test import TestCase
from django.contrib.messages import get_messages
from .models import Account

class BalanceTransferViewTests(TestCase):

    def setUp(self):
        self.url = reverse("balance-transaction")
        self.sender = Account.objects.create(ref="1", name="John", balance=1000.0)
        self.recipient = Account.objects.create(ref="2", name="Jane", balance=500.0)

    def post_data(self, data):
        response = self.client.post(self.url, data)
        messages = list(get_messages(response.wsgi_request))
        return response, messages

    def test_valid_transaction(self):
        data = {
            "sender": self.sender.ref,
            "recepient": self.recipient.ref,
            "amount": 100.0
        }
        response, messages = self.post_data(data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.url)
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "Transaction Completed Successfully")
        self.sender.refresh_from_db()
        self.recipient.refresh_from_db()
        self.assertEqual(self.sender.balance, 900.0)
        self.assertEqual(self.recipient.balance, 600.0)

    def test_non_existent_account(self):
        data = {
            "sender": "999",
            "recepient": self.recipient.ref,
            "amount": 100.0
        }
        response, messages = self.post_data(data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.url)
        self.assertEqual(len(messages), 1)
        self.assertIn(f"Sender with reference '{data['sender']}' does not exist.", str(messages[0]))

    def test_empty_account_reference(self):
        data = {
            "sender": "",
            "recepient": self.recipient.ref,
            "amount": 100.0
        }
        response, messages = self.post_data(data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.url)
        self.assertEqual(len(messages), 1)
        self.assertIn("This field is required.", str(messages[0]))

    def test_empty_amount(self):
        data = {
            "sender": self.sender.ref,
            "recepient": self.recipient.ref,
            "amount": ""
        }
        response, messages = self.post_data(data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.url)
        self.assertEqual(len(messages), 1)
        self.assertIn("This field is required.", str(messages[0]))

    def test_negative_amount(self):
        data = {
            "sender": self.sender.ref,
            "recepient": self.recipient.ref,
            "amount": -100.0
        }
        response, messages = self.post_data(data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.url)
        self.assertEqual(len(messages), 1)
        self.assertIn("Ensure this value is greater than or equal to 5.0", str(messages[0]))

    def test_amount_too_large(self):
        data = {
            "sender": self.sender.ref,
            "recepient": self.recipient.ref,
            "amount": 10000000000000000000.0 
        }
        response, messages = self.post_data(data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.url)
        self.assertEqual(len(messages), 1)
        self.assertIn("Ensure that there are no more than 18 digits before the decimal point.", str(messages[0]))

    def test_amount_greater_than_balance(self):
        data = {
            "sender": self.sender.ref,
            "recepient": self.recipient.ref,
            "amount": 2000.0 
        }
        response, messages = self.post_data(data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.url)
        self.assertEqual(len(messages), 1)
        self.assertIn("Error making transaction", str(messages[0]))
        self.sender.refresh_from_db()
        self.recipient.refresh_from_db()
        self.assertEqual(self.sender.balance, 1000.0) 
        self.assertEqual(self.recipient.balance, 500.0)  
