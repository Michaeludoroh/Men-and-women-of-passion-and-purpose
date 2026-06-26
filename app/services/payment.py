import requests
from flask import current_app
from ..utils.urls import external_route


def initialize_paystack_payment(email: str, amount: float, reference: str):
    """
    Initialize Paystack transaction.
    Amount is converted to kobo.
    """
    secret = current_app.config.get("PAYSTACK_SECRET_KEY")
    if not secret:
        return {
            "status": False,
            "message": "PAYSTACK_SECRET_KEY is not configured.",
            "data": {},
        }

    url = "https://api.paystack.co/transaction/initialize"
    headers = {"Authorization": f"Bearer {secret}", "Content-Type": "application/json"}
    payload = {"email": email, "amount": int(amount * 100), "reference": reference}

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=20)
        return response.json()
    except requests.RequestException as exc:
        return {"status": False, "message": str(exc), "data": {}}


def initialize_flutterwave_payment(email: str, amount: float, reference: str):
    secret = current_app.config.get("FLUTTERWAVE_SECRET_KEY")
    if not secret:
        return {
            "status": False,
            "message": "FLUTTERWAVE_SECRET_KEY is not configured.",
            "data": {},
        }

    url = "https://api.flutterwave.com/v3/payments"
    headers = {"Authorization": f"Bearer {secret}", "Content-Type": "application/json"}
    payload = {
        "tx_ref": reference,
        "amount": amount,
        "currency": "NGN",
        "redirect_url": external_route("giving.payment_success"),
        "customer": {"email": email},
        "payment_options": "card, ussd, mobilemoney"
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=20)
        data = response.json()
        if data['status'] == 'success':
            return {"status": True, "data": {"authorization_url": data['data']['link']}}
        return {"status": False, "message": data.get('message', 'Failed')}
    except requests.RequestException as exc:
        return {"status": False, "message": str(exc), "data": {}}


def verify_payment(gateway: str, reference: str):
    if gateway == 'paystack':
        secret = current_app.config.get("PAYSTACK_SECRET_KEY")
        url = f"https://api.paystack.co/transaction/verify/{reference}"
        headers = {"Authorization": f"Bearer {secret}", "Content-Type": "application/json"}
        try:
            response = requests.get(url, headers=headers, timeout=20)
            data = response.json()
            return data['data']['status'] == 'success'
        except:
            return False
    elif gateway == 'flutterwave':
        secret = current_app.config.get("FLUTTERWAVE_SECRET_KEY")
        url = f"https://api.flutterwave.com/v3/transactions/{reference}/verify"
        headers = {"Authorization": f"Bearer {secret}", "Content-Type": "application/json"}
        try:
            response = requests.get(url, headers=headers, timeout=20)
            data = response.json()
            return data['status'] == 'success' and data['data']['status'] == 'successful'
        except:
            return False
    return False
