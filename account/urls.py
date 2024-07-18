from django.urls import path
from .views import *

urlpatterns = [
    path("", AccountListView.as_view(),name="account-list"),
    path("account-details/<int:pk>", AccountDetailsView.as_view(),name="account-details"),
    path("import-accounts/",ImportAccountsView.as_view(),name='import-accounts')
    ]


