from django.urls import path
from .views import *

urlpatterns = [
    path("balance-transfer/", BalanceTransferView.as_view(),name="balance-transaction"),
    ]
