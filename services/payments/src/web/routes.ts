import express from 'express';
import { 
  startQuote, 
  finishPayment, 
  listSellers, 
  upsertSeller,
  getPaymentStatus,
  createIncomingPayment,
  listPendingPayments,
  getOfferPayments
} from './routes_handlers';

const router = express.Router();

// Sellers admin (simple)
router.get('/sellers', listSellers);
router.post('/sellers', upsertSeller);

// Buyer flow
router.post('/offers/:offerId/quotes/start', startQuote);
router.get('/payments/finish', finishPayment);

// Payment status and management
router.get('/payments/:pendingId/status', getPaymentStatus);
router.get('/payments/pending', listPendingPayments);
router.get('/offers/:offerId/payments', getOfferPayments);

// Django integration endpoints
router.post('/api/payments/incoming', createIncomingPayment);

export default router;


