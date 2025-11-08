// Payment Routes
// Define las rutas HTTP para los endpoints de pagos

import express from 'express';
import {
  createIncomingPayment,
  createOutgoingPayment,
  healthCheck,
  paymentWebhook
} from '../controllers/paymentsController.js';

const router = express.Router();

// Health check
router.get('/health', healthCheck);

// Payment endpoints
router.post('/api/payments/incoming', createIncomingPayment);
router.post('/api/payments/outgoing', createOutgoingPayment);

// Webhook endpoint
router.post('/api/webhooks/payment-completed', paymentWebhook);

export default router;
