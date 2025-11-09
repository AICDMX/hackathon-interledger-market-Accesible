"""Utility functions for interacting with the payments service."""
import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


def create_incoming_payment(amount, description):
    """
    Create an incoming payment (escrow) via the payments service.
    
    Args:
        amount: Amount as string or Decimal (will be converted to string)
        description: Description of the payment
        
    Returns:
        dict with 'success', 'payment_id', and optionally 'error'
    """
    try:
        payments_url = f"{settings.PAYMENTS_SERVICE_URL}/api/payments/incoming"
        
        # Convert amount to string if needed
        amount_str = str(amount)
        
        payload = {
            'amount': amount_str,
            'description': description or 'Job funding'
        }
        
        logger.info(f"Creating incoming payment: {payload}")
        
        response = requests.post(
            payments_url,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                return {
                    'success': True,
                    'payment_id': data.get('paymentId') or data.get('payment_id'),
                    'data': data
                }
            else:
                return {
                    'success': False,
                    'error': data.get('error', 'Unknown error from payments service')
                }
        else:
            error_msg = f"Payments service returned status {response.status_code}"
            try:
                error_data = response.json()
                error_msg = error_data.get('error', error_msg)
            except:
                error_msg = response.text or error_msg
            
            logger.error(f"Failed to create incoming payment: {error_msg}")
            return {
                'success': False,
                'error': error_msg
            }
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Error connecting to payments service: {str(e)}")
        return {
            'success': False,
            'error': f"Could not connect to payments service: {str(e)}"
        }
    except Exception as e:
        logger.error(f"Unexpected error creating incoming payment: {str(e)}")
        return {
            'success': False,
            'error': f"Unexpected error: {str(e)}"
        }
