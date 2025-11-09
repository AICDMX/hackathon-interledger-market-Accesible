"""Utility functions for interacting with the payments service."""
import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


def start_quote(offer_id, seller_id, buyer_wallet_address_url, amount):
    """
    Start a buyer quote with the payments service and return the redirect URL and payment URL.

    Args:
        offer_id: The offer/job ID used as path parameter on the payments service.
        seller_id: The configured seller identifier in the payments service.
        buyer_wallet_address_url: The buyer's wallet address URL.
        amount: Amount to pay (string or Decimal).

    Returns:
        dict with 'success' and either 'redirect_url', 'payment_url', 'pending_id' or 'error'
    """
    try:
        payments_url = f"{settings.PAYMENTS_SERVICE_URL}/offers/{offer_id}/quotes/start"
        payload = {
            "sellerId": seller_id,
            "buyerWalletAddressUrl": buyer_wallet_address_url,
            "amount": str(amount),
        }
        logger.info(f"Starting quote via payments service: {payments_url} payload={payload}")
        response = requests.post(
            payments_url,
            json=payload,
            timeout=30
        )
        if response.status_code == 200:
            data = response.json()
            redirect_url = data.get('redirectUrl')
            payment_url = data.get('paymentUrl', redirect_url)
            pending_id = data.get('pendingId')
            if redirect_url:
                return {
                    "success": True, 
                    "redirect_url": redirect_url,
                    "payment_url": payment_url,
                    "pending_id": pending_id,
                    "data": data
                }
            return {"success": False, "error": "Missing redirectUrl in payments service response"}
        # Non-200s
        try:
            err = response.json().get('error')
        except Exception:
            err = response.text
        return {"success": False, "error": err or f"Payments service error {response.status_code}"}
    except requests.exceptions.RequestException as e:
        logger.error(f"Error connecting to payments service: {str(e)}")
        return {"success": False, "error": f"Could not connect to payments service: {str(e)}"}
    except Exception as e:
        logger.error(f"Unexpected error starting quote: {str(e)}")
        return {"success": False, "error": f"Unexpected error: {str(e)}"}


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


def get_wallet_profile(wallet_address_url):
    """
    Fetch wallet profile from the payments service using Open Payments API.
    
    Args:
        wallet_address_url: The wallet address URL to fetch profile for
        
    Returns:
        dict with 'success', 'wallet' (containing profile data), and optionally 'error'
    """
    try:
        payments_url = f"{settings.PAYMENTS_SERVICE_URL}/api/wallet/profile"
        
        payload = {
            'walletAddressUrl': wallet_address_url
        }
        
        logger.info(f"Fetching wallet profile for: {wallet_address_url}")
        
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
                    'wallet': data.get('wallet'),
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
            
            logger.error(f"Failed to fetch wallet profile: {error_msg}")
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
        logger.error(f"Unexpected error fetching wallet profile: {str(e)}")
        return {
            'success': False,
            'error': f"Unexpected error: {str(e)}"
        }
