"""
Squad API Integration
Handles payment processing through Squad's infrastructure.

Why separate module?
- Easy to mock for testing
- Can switch providers without touching business logic
- Centralized error handling

MVP: Basic transfer functionality
Production: Webhooks, reconciliation, batch transfers
"""

import requests
import logging
from typing import Dict, Optional, Tuple
from app.core.config import settings
from datetime import datetime

logger = logging.getLogger(__name__)


class SquadAPIError(Exception):
    """Custom exception for Squad API failures."""
    pass


class SquadPaymentProcessor:
    """Handles payment processing via Squad API."""
    
    def __init__(self):
        self.api_key = settings.SQUAD_API_KEY
        self.public_key = settings.SQUAD_PUBLIC_KEY
        self.base_url = settings.SQUAD_API_BASE_URL
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def create_transfer(
        self,
        recipient_bank_code: str,
        recipient_account_number: str,
        amount_in_cents: int,
        employee_name: str,
        employee_id: str,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Create a bank transfer through Squad.
        
        Args:
            recipient_bank_code: Bank code (e.g., "001" for CBN)
            recipient_account_number: 10-digit account number
            amount_in_cents: Amount in kobo (e.g., 100000 = 1000 NGN)
            employee_name: Recipient name
            employee_id: Our internal employee ID
            metadata: Additional data to track
            
        Returns:
            Squad API response with transaction_id
            
        Raises:
            SquadAPIError: If transfer fails
            
        MVP Example:
        response = processor.create_transfer(
            recipient_bank_code="001",
            recipient_account_number="1234567890",
            amount_in_cents=50000000,  # 500,000 NGN
            employee_name="John Doe",
            employee_id="emp-123"
        )
        # Returns: {
        #     "status": "success",
        #     "data": {
        #         "transaction_id": "TXN-123456",
        #         "status": "pending"
        #     }
        # }
        """
        try:
            endpoint = f"{self.base_url}/v1/transfers"
            
            # Build request payload
            payload = {
                "account_number": recipient_account_number,
                "bank_code": recipient_bank_code,
                "amount_in_kobo": amount_in_cents,
                "narration": f"Salary: {employee_name}",
                "currency": "NGN",
                "reference": f"emp-{employee_id}-{datetime.utcnow().timestamp()}",
                "metadata": metadata or {}
            }
            
            # Log request (without sensitive data)
            logger.info(
                f"Squad transfer initiated: {employee_name}, "
                f"amount={amount_in_cents/100} NGN"
            )
            
            # Make request
            response = requests.post(
                endpoint,
                json=payload,
                headers=self.headers,
                timeout=30
            )
            
            # Check response
            if response.status_code not in [200, 201]:
                error_msg = response.text
                logger.error(f"Squad API error: {error_msg}")
                raise SquadAPIError(f"Transfer failed: {error_msg}")
            
            data = response.json()
            
            # Success response format (check Squad docs for actual format)
            if data.get("status") == "success":
                transaction_data = data.get("data", {})
                logger.info(f"Transfer successful: {transaction_data.get('transaction_id')}")
                return {
                    "success": True,
                    "transaction_id": transaction_data.get("transaction_id"),
                    "reference": transaction_data.get("reference"),
                    "status": transaction_data.get("status"),
                    "amount": amount_in_cents / 100,  # Convert back to NGN
                }
            else:
                raise SquadAPIError(f"Transfer rejected: {data.get('message')}")
        
        except requests.RequestException as e:
            logger.error(f"Squad API connection error: {str(e)}")
            raise SquadAPIError(f"Network error: {str(e)}")
    
    def verify_transfer(self, transaction_id: str) -> Dict:
        """
        Verify status of a transfer.
        
        Args:
            transaction_id: Squad transaction ID
            
        Returns:
            Transfer status and details
            
        Raises:
            SquadAPIError: If verification fails
        """
        try:
            endpoint = f"{self.base_url}/v1/transfers/{transaction_id}"
            
            response = requests.get(
                endpoint,
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code != 200:
                raise SquadAPIError(f"Verification failed: {response.text}")
            
            data = response.json()
            logger.info(f"Transfer verified: {transaction_id}, status={data.get('status')}")
            
            return {
                "transaction_id": transaction_id,
                "status": data.get("status"),
                "amount": data.get("amount"),
                "recipient": data.get("recipient"),
                "timestamp": data.get("timestamp")
            }
        
        except requests.RequestException as e:
            logger.error(f"Squad verification failed: {str(e)}")
            raise SquadAPIError(f"Verification error: {str(e)}")
    
    def handle_webhook(self, payload: Dict, signature: str) -> bool:
        """
        Handle Squad webhook for transfer status updates.
        
        Args:
            payload: Webhook payload from Squad
            signature: X-Squad-Signature header
            
        Returns:
            True if webhook is valid and processed
            
        Production: Implement HMAC-SHA256 verification
        """
        # MVP: Skip signature verification
        # Production: Verify signature with SQUAD_WEBHOOK_SECRET
        
        try:
            transaction_id = payload.get("transaction_id")
            status = payload.get("status")
            
            logger.info(f"Webhook received: TXN={transaction_id}, status={status}")
            
            # Update PayrollRecord in database
            # This would be called from a route handler
            return True
        
        except Exception as e:
            logger.error(f"Webhook processing failed: {str(e)}")
            return False


# Convenience functions for service layer

def process_payment(
    recipient_bank_code: str,
    recipient_account_number: str,
    amount_in_cents: int,
    employee_name: str,
    employee_id: str
) -> Tuple[bool, str, Optional[str]]:
    """
    High-level payment processing function.
    
    Returns:
        (success: bool, message: str, transaction_id: Optional[str])
    """
    try:
        processor = SquadPaymentProcessor()
        result = processor.create_transfer(
            recipient_bank_code=recipient_bank_code,
            recipient_account_number=recipient_account_number,
            amount_in_cents=amount_in_cents,
            employee_name=employee_name,
            employee_id=employee_id
        )
        
        return (
            True,
            f"Payment of {amount_in_cents/100} NGN processed successfully",
            result.get("transaction_id")
        )
    
    except SquadAPIError as e:
        return (False, str(e), None)
