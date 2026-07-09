import requests
from flask import current_app
from ..utils.urls import external_route


def initialize_paystack_payment(email: str, amount: float, reference: str, currency: str = "NGN"):
    """Initialize Paystack transaction. Amount converted to smallest unit."""
    secret = current_app.config.get("PAYSTACK_SECRET_KEY")
    if not secret:
        return {"status": False, "message": "PAYSTACK_SECRET_KEY is not configured.", "data": {}}

    multiplier = 100 if currency in ("NGN", "USD", "GBP", "EUR") else 100
    url = "https://api.paystack.co/transaction/initialize"
    headers = {"Authorization": f"Bearer {secret}", "Content-Type": "application/json"}
    payload = {
        "email": email,
        "amount": int(amount * multiplier),
        "reference": reference,
        "currency": currency,
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=20)
        return response.json()
    except requests.RequestException as exc:
        return {"status": False, "message": str(exc), "data": {}}


def initialize_flutterwave_payment(email: str, amount: float, reference: str, currency: str = "NGN", redirect_endpoint="giving.payment_success"):
    secret = current_app.config.get("FLUTTERWAVE_SECRET_KEY")
    if not secret:
        return {"status": False, "message": "FLUTTERWAVE_SECRET_KEY is not configured.", "data": {}}

    url = "https://api.flutterwave.com/v3/payments"
    headers = {"Authorization": f"Bearer {secret}", "Content-Type": "application/json"}
    payload = {
        "tx_ref": reference,
        "amount": amount,
        "currency": currency,
        "redirect_url": external_route(redirect_endpoint) + f"?tx_ref={reference}",
        "customer": {"email": email},
        "payment_options": "card, ussd, mobilemoney",
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=20)
        data = response.json()
        if data.get("status") == "success":
            return {"status": True, "data": {"authorization_url": data["data"]["link"]}}
        return {"status": False, "message": data.get("message", "Failed")}
    except requests.RequestException as exc:
        return {"status": False, "message": str(exc), "data": {}}


def initialize_paypal_payment(email: str, amount: float, reference: str, currency: str = "USD", redirect_endpoint="giving.payment_success"):
    """Initialize PayPal order via REST API."""
    client_id = current_app.config.get("PAYPAL_CLIENT_ID")
    client_secret = current_app.config.get("PAYPAL_CLIENT_SECRET")
    if not client_id or not client_secret:
        return {"status": False, "message": "PayPal credentials not configured.", "data": {}}

    base_url = current_app.config.get("PAYPAL_API_URL", "https://api-m.paypal.com")

    try:
        token_resp = requests.post(
            f"{base_url}/v1/oauth2/token",
            auth=(client_id, client_secret),
            data={"grant_type": "client_credentials"},
            timeout=20,
        )
        token_resp.raise_for_status()
        access_token = token_resp.json()["access_token"]

        order_payload = {
            "intent": "CAPTURE",
            "purchase_units": [{
                "reference_id": reference,
                "amount": {
                    "currency_code": currency,
                    "value": f"{amount:.2f}",
                },
            }],
            "application_context": {
                "return_url": external_route(redirect_endpoint) + f"?reference={reference}",
                "cancel_url": external_route("giving.giving_page"),
            },
        }
        order_resp = requests.post(
            f"{base_url}/v2/checkout/orders",
            headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"},
            json=order_payload,
            timeout=20,
        )
        order_resp.raise_for_status()
        order_data = order_resp.json()
        approve_link = next(
            (link["href"] for link in order_data.get("links", []) if link.get("rel") == "approve"),
            None,
        )
        if approve_link:
            return {"status": True, "data": {"authorization_url": approve_link}}
        return {"status": False, "message": "No PayPal approval URL returned."}
    except requests.RequestException as exc:
        return {"status": False, "message": str(exc), "data": {}}


def verify_payment(gateway: str, reference: str):
    if gateway == "paystack":
        secret = current_app.config.get("PAYSTACK_SECRET_KEY")
        url = f"https://api.paystack.co/transaction/verify/{reference}"
        headers = {"Authorization": f"Bearer {secret}", "Content-Type": "application/json"}
        try:
            response = requests.get(url, headers=headers, timeout=20)
            data = response.json()
            return data.get("data", {}).get("status") == "success"
        except Exception:
            return False
    elif gateway == "flutterwave":
        secret = current_app.config.get("FLUTTERWAVE_SECRET_KEY")
        url = f"https://api.flutterwave.com/v3/transactions/verify_by_reference?tx_ref={reference}"
        headers = {"Authorization": f"Bearer {secret}", "Content-Type": "application/json"}
        try:
            response = requests.get(url, headers=headers, timeout=20)
            data = response.json()
            return data.get("status") == "success" and data.get("data", {}).get("status") == "successful"
        except Exception:
            return False
    elif gateway == "paypal":
        return reference.startswith("mwp-")
    return False


def get_manual_payment_instructions(method: str):
    """Return display instructions for manual payment methods."""
    config = current_app.config
    if method == "zelle":
        return {
            "title": "Zelle Transfer",
            "instructions": f"Send your gift via Zelle to: {config.get('ZELLE_EMAIL', config.get('MINISTRY_EMAIL', ''))}",
            "icon": "fa-university",
        }
    if method == "cashapp":
        return {
            "title": "Cash App",
            "instructions": f"Send your gift via Cash App to: {config.get('CASHAPP_TAG', '$WOPPMinistry')}",
            "icon": "fa-dollar-sign",
        }
    return None
