"""
Prodamus payment integration service
"""
import hashlib
import hmac
import json
import logging
from typing import Dict, Optional
from urllib.parse import urlencode

from bot.config import PRODAMUS_SECRET, PRODAMUS_SHOP_ID, PRODAMUS_BASE_URL

logger = logging.getLogger(__name__)


def create_payment_link(
        order_id: str,
        amount: int,
        description: str,
        customer_email: str = None,
        customer_phone: str = None,
        success_url: str = None,
        fail_url: str = None
) -> str:
    """
    Create Prodamus payment link

    Args:
        order_id: Unique order identifier
        amount: Payment amount in rubles
        description: Payment description
        customer_email: Customer email (optional)
        customer_phone: Customer phone (optional)
        success_url: URL to redirect after successful payment
        fail_url: URL to redirect after failed payment

    Returns:
        Payment URL string
    """
    params = {
        "order_id": order_id,
        "products[0][name]": description,
        "products[0][price]": str(amount),
        "products[0][quantity]": "1",
        "do": "pay",
    }

    if customer_email:
        params["customer_email"] = customer_email

    if customer_phone:
        params["customer_phone"] = customer_phone

    if success_url:
        params["success_url"] = success_url

    if fail_url:
        params["fail_url"] = fail_url

    # Generate signature
    params["signature"] = generate_signature(params)

    # Build URL
    payment_url = f"{PRODAMUS_BASE_URL}/{PRODAMUS_SHOP_ID}?{urlencode(params)}"

    logger.info(f"Created payment link for order {order_id}: {amount} RUB")

    return payment_url


def generate_signature(params: Dict) -> str:
    """Generate HMAC signature for Prodamus request"""
    # Sort params and create string
    sorted_params = sorted(params.items())
    sign_string = "&".join(f"{k}={v}" for k, v in sorted_params)

    # Create HMAC-SHA256 signature
    signature = hmac.new(
        PRODAMUS_SECRET.encode('utf-8'),
        sign_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

    return signature


def verify_webhook_signature(data: Dict, received_signature: str) -> bool:
    """
    Verify Prodamus webhook signature

    Args:
        data: Webhook payload data
        received_signature: Signature from webhook headers

    Returns:
        True if signature is valid
    """
    try:
        # Create signature from data
        data_copy = dict(data)
        if 'signature' in data_copy:
            del data_copy['signature']

        calculated_signature = generate_signature(data_copy)

        return hmac.compare_digest(calculated_signature, received_signature)

    except Exception as e:
        logger.error(f"Error verifying webhook signature: {e}")
        return False


def parse_webhook_data(raw_data: bytes) -> Optional[Dict]:
    """
    Parse webhook data from Prodamus

    Args:
        raw_data: Raw request body

    Returns:
        Parsed data dict or None
    """
    try:
        # Try JSON first
        data = json.loads(raw_data.decode('utf-8'))
        return data
    except json.JSONDecodeError:
        pass

    try:
        # Try form data
        from urllib.parse import parse_qs
        parsed = parse_qs(raw_data.decode('utf-8'))
        return {k: v[0] if len(v) == 1 else v for k, v in parsed.items()}
    except Exception as e:
        logger.error(f"Error parsing webhook data: {e}")
        return None


def is_payment_successful(webhook_data: Dict) -> bool:
    """
    Check if payment was successful based on webhook data

    Args:
        webhook_data: Parsed webhook payload

    Returns:
        True if payment was successful
    """
    # Check payment status
    status = webhook_data.get('payment_status', '').lower()
    return status in ('success', 'paid', 'completed')


def get_order_id_from_webhook(webhook_data: Dict) -> Optional[str]:
    """Extract order_id from webhook data"""
    return webhook_data.get('order_id') or webhook_data.get('order_num')


def get_amount_from_webhook(webhook_data: Dict) -> Optional[int]:
    """Extract payment amount from webhook data"""
    try:
        amount = webhook_data.get('sum') or webhook_data.get('amount')
        return int(float(amount)) if amount else None
    except (ValueError, TypeError):
        return None
