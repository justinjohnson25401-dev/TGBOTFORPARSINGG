"""
YooMoney API service for payment verification
"""
import logging
import aiohttp
from datetime import datetime, timedelta
from typing import Optional, Dict, List

logger = logging.getLogger(__name__)

# YooMoney API endpoints
YOOMONEY_API_URL = "https://yoomoney.ru/api"
YOOMONEY_PAYMENT_URL = "https://yoomoney.ru/to"


class YooMoneyService:
    """Service for interacting with YooMoney API"""

    def __init__(self, access_token: str, wallet_number: str):
        self.access_token = access_token
        self.wallet_number = wallet_number
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/x-www-form-urlencoded"
        }

    def get_payment_url(self, amount: int, label: str = None) -> str:
        """
        Generate payment URL for YooMoney

        Args:
            amount: Payment amount in rubles
            label: Optional label for tracking payment

        Returns:
            Payment URL string
        """
        url = f"{YOOMONEY_PAYMENT_URL}/{self.wallet_number}"
        params = [f"sum={amount}"]
        if label:
            params.append(f"label={label}")

        if params:
            url += "?" + "&".join(params)

        return url

    async def get_account_info(self) -> Optional[Dict]:
        """Get account information"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{YOOMONEY_API_URL}/account-info",
                    headers=self.headers
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f"Failed to get account info: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Error getting account info: {e}")
            return None

    async def get_operation_history(
        self,
        records: int = 50,
        from_date: datetime = None,
        label: str = None
    ) -> List[Dict]:
        """
        Get operation history

        Args:
            records: Number of records to fetch (max 100)
            from_date: Start date for filtering
            label: Filter by label

        Returns:
            List of operations
        """
        try:
            data = {
                "type": "deposition",  # Only incoming payments
                "records": min(records, 100)
            }

            if from_date:
                data["from"] = from_date.strftime("%Y-%m-%dT%H:%M:%S")

            if label:
                data["label"] = label

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{YOOMONEY_API_URL}/operation-history",
                    headers=self.headers,
                    data=data
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get("operations", [])
                    else:
                        logger.error(f"Failed to get operation history: {response.status}")
                        return []
        except Exception as e:
            logger.error(f"Error getting operation history: {e}")
            return []

    async def get_operation_details(self, operation_id: str) -> Optional[Dict]:
        """Get details of specific operation"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{YOOMONEY_API_URL}/operation-details",
                    headers=self.headers,
                    data={"operation_id": operation_id}
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f"Failed to get operation details: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Error getting operation details: {e}")
            return None

    async def find_payment(
        self,
        amount: int,
        minutes_ago: int = 30,
        tolerance: int = 100,
        used_operation_ids: List[str] = None
    ) -> Optional[Dict]:
        """
        Find payment matching the criteria

        Args:
            amount: Expected amount in rubles
            minutes_ago: How far back to search
            tolerance: Acceptable overpayment amount
            used_operation_ids: List of already used operation IDs

        Returns:
            Payment info dict with keys:
            - found: bool
            - exact: bool (True if exact amount)
            - overpaid: int (amount overpaid, 0 if exact or less)
            - underpaid: int (amount underpaid, 0 if exact or more)
            - operation_id: str
            - actual_amount: float
        """
        if used_operation_ids is None:
            used_operation_ids = []

        from_date = datetime.now() - timedelta(minutes=minutes_ago)
        operations = await self.get_operation_history(records=50, from_date=from_date)

        for op in operations:
            # Skip already used payments
            if op.get("operation_id") in used_operation_ids:
                continue

            # Check if it's incoming payment
            if op.get("direction") != "in":
                continue

            op_amount = float(op.get("amount", 0))

            # Exact payment
            if op_amount == amount:
                return {
                    "found": True,
                    "exact": True,
                    "overpaid": 0,
                    "underpaid": 0,
                    "operation_id": op.get("operation_id"),
                    "actual_amount": op_amount
                }

            # Overpayment within tolerance (small overpay is OK)
            if op_amount > amount and op_amount <= amount + tolerance:
                return {
                    "found": True,
                    "exact": False,
                    "overpaid": int(op_amount - amount),
                    "underpaid": 0,
                    "operation_id": op.get("operation_id"),
                    "actual_amount": op_amount
                }

            # Large overpayment (still accept but note it)
            if op_amount > amount + tolerance:
                return {
                    "found": True,
                    "exact": False,
                    "overpaid": int(op_amount - amount),
                    "underpaid": 0,
                    "operation_id": op.get("operation_id"),
                    "actual_amount": op_amount,
                    "large_overpay": True
                }

            # Underpayment - don't accept, but report
            if op_amount > 0 and op_amount < amount:
                # Check if this could be a partial payment for this order
                # We'll return info about underpayment
                return {
                    "found": False,
                    "exact": False,
                    "overpaid": 0,
                    "underpaid": int(amount - op_amount),
                    "operation_id": op.get("operation_id"),
                    "actual_amount": op_amount,
                    "partial": True
                }

        # No matching payment found
        return {
            "found": False,
            "exact": False,
            "overpaid": 0,
            "underpaid": 0,
            "operation_id": None,
            "actual_amount": 0
        }


# Global service instance
_yoomoney_service: Optional[YooMoneyService] = None


def get_yoomoney_service() -> Optional[YooMoneyService]:
    """Get YooMoney service instance"""
    global _yoomoney_service
    return _yoomoney_service


def init_yoomoney_service(access_token: str, wallet_number: str):
    """Initialize YooMoney service"""
    global _yoomoney_service
    _yoomoney_service = YooMoneyService(access_token, wallet_number)
    logger.info("YooMoney service initialized")


async def verify_yoomoney_token(access_token: str, wallet_number: str) -> bool:
    """Verify that YooMoney token is valid"""
    try:
        service = YooMoneyService(access_token, wallet_number)
        info = await service.get_account_info()
        if info:
            logger.info(f"YooMoney account verified: {info.get('account', 'unknown')}")
            return True
        return False
    except Exception as e:
        logger.error(f"Failed to verify YooMoney token: {e}")
        return False
