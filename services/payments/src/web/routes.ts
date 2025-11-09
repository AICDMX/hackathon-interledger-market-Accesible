import express from 'express';
import { startQuote, finishPayment, listSellers, upsertSeller } from './routes_handlers';

const router = express.Router();

// Sellers admin (simple)
router.get('/sellers', listSellers);
router.post('/sellers', upsertSeller);

// Buyer flow
router.post('/offers/:offerId/quotes/start', startQuote);
router.get('/payments/finish', finishPayment);

export default router;


