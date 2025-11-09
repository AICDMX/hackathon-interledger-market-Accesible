"""Webhook handlers for payment notifications from the payments service."""
import json
import logging
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .models import Job

logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def payment_webhook(request):
    """
    Handle payment completion/failure webhooks from the payments service.
    
    Expected payload:
    {
        "type": "payment.completed" | "payment.failed",
        "pendingId": "string",
        "offerId": "string",
        "status": "paid" | "failed",
        "outgoingPaymentId": "string" (optional),
        "timestamp": "ISO8601 string"
    }
    """
    try:
        # Parse webhook payload
        payload = json.loads(request.body)
        event_type = payload.get('type')
        pending_id = payload.get('pendingId')
        offer_id = payload.get('offerId')
        status = payload.get('status')
        outgoing_payment_id = payload.get('outgoingPaymentId')
        timestamp = payload.get('timestamp')
        
        logger.info(
            f"[webhook] Received {event_type} for offer {offer_id}, "
            f"pending {pending_id}, status {status}"
        )
        
        # Validate required fields
        if not all([event_type, pending_id, offer_id, status]):
            logger.error("[webhook] Missing required fields in payload")
            return HttpResponseBadRequest("Missing required fields")
        
        # Look up the job by offer_id (which is the job pk)
        try:
            job = Job.objects.get(pk=int(offer_id))
        except (Job.DoesNotExist, ValueError):
            logger.error(f"[webhook] Job not found for offer_id {offer_id}")
            return JsonResponse({
                'success': False,
                'error': 'Job not found'
            }, status=404)
        
        # Handle payment completion
        if event_type == 'payment.completed' and status == 'paid':
            # Update job with payment confirmation
            job.payment_id = outgoing_payment_id or pending_id
            job.contract_completed = True
            
            # If job is in 'reviewing' state and payment confirmed, mark as complete
            if job.status == 'reviewing':
                job.status = 'complete'
            
            job.save()
            
            logger.info(
                f"[webhook] Payment confirmed for job {job.pk} ({job.title}). "
                f"Contract marked as completed."
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Payment confirmed',
                'job_id': job.pk,
                'job_status': job.status
            })
        
        # Handle payment failure
        elif event_type == 'payment.failed' and status == 'failed':
            logger.warning(
                f"[webhook] Payment failed for job {job.pk} ({job.title}). "
                f"Pending ID: {pending_id}"
            )
            
            # Optionally mark job as having payment issues
            # You might want to add a field to track this
            
            return JsonResponse({
                'success': True,
                'message': 'Payment failure recorded',
                'job_id': job.pk
            })
        
        else:
            logger.error(f"[webhook] Unknown event type or status: {event_type}, {status}")
            return HttpResponseBadRequest("Unknown event type or status")
            
    except json.JSONDecodeError:
        logger.error("[webhook] Invalid JSON in request body")
        return HttpResponseBadRequest("Invalid JSON")
    except Exception as e:
        logger.error(f"[webhook] Unexpected error: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': 'Internal server error'
        }, status=500)
