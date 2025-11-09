import axios from 'axios';

export type WebhookEvent = {
  type: 'payment.completed' | 'payment.failed';
  pendingId: string;
  offerId: string;
  status: 'paid' | 'failed';
  outgoingPaymentId?: string;
  timestamp: string;
};

export async function notifyDjango(event: WebhookEvent): Promise<void> {
  const djangoUrl = process.env.DJANGO_BASE_URL;
  
  if (!djangoUrl) {
    // eslint-disable-next-line no-console
    console.log('[webhook] DJANGO_BASE_URL not configured, skipping notification');
    return;
  }

  try {
    const webhookUrl = `${djangoUrl}/api/webhooks/payments`;
    
    // eslint-disable-next-line no-console
    console.log(`[webhook] Sending ${event.type} to ${webhookUrl}`, event);
    
    await axios.post(webhookUrl, event, {
      headers: {
        'Content-Type': 'application/json',
        // Add authentication header if needed
        // 'Authorization': `Bearer ${process.env.WEBHOOK_SECRET}`
      },
      timeout: 10000
    });
    
    // eslint-disable-next-line no-console
    console.log(`[webhook] Successfully notified Django: ${event.type} for ${event.pendingId}`);
  } catch (error: any) {
    // eslint-disable-next-line no-console
    console.error('[webhook] Failed to notify Django:', error.message);
    // Don't throw - webhook failures shouldn't break payment flow
  }
}
