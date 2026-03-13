import requests
import uuid
from django.conf import settings
from django.shortcuts import redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required


@login_required
def initiate_payment(request):

    amount = request.GET.get("amount")

    if not amount:
        return HttpResponse("Amount missing")

    tx_ref = str(uuid.uuid4())

    request.session["tx_ref"] = tx_ref

    headers = {
        "Authorization": f"Bearer {settings.FLUTTER_SECRET_KEY}",
        "Content-Type": "application/json",
    }

    data = {
        "tx_ref": tx_ref,
        "amount": str(amount),
        "currency": "USD",
        "redirect_url": "http://127.0.0.1:8000/payment/verify/",
        "customer": {
            "email": request.user.email or "test@email.com",
            "name": request.user.username,
        },
        "customizations": {
            "title": "ShopMore Payment",
            "description": "Checkout payment",
        },
    }

    response = requests.post(
        "https://api.flutterwave.com/v3/payments",
        json=data,
        headers=headers,
    )

    res = response.json()

    if res.get("status") == "success":
        return redirect(res["data"]["link"])

    return HttpResponse("Flutterwave error")


import requests
from django.conf import settings
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required


@login_required
def verify_payment(request):

    tx_ref = request.session.get("tx_ref")

    if not tx_ref:
        return redirect("cart")

    headers = {
        "Authorization": f"Bearer {settings.FLUTTER_SECRET_KEY}",
    }

    url = f"https://api.flutterwave.com/v3/transactions/verify_by_reference?tx_ref={tx_ref}"

    response = requests.get(url, headers=headers)

    res = response.json()

    if res.get("status") == "success":
        return redirect("/order/success/1/")

    return redirect("cart")
