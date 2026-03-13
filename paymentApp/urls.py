from django.urls import path
from . import views

app_name = "payment"

urlpatterns = [
    path("", views.initiate_payment, name="initiate"),
    path("verify/", views.verify_payment, name="verify"),
]
