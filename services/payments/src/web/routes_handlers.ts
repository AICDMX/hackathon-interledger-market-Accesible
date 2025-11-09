import { Request, Response } from 'express';
import { startQuoteFlow, completePayment, createIncomingPaymentForJob } from '../workflow/paymentsService';
import { sellersRepo } from '../workbench/sellersRepo';
import { pendingRepo } from '../workbench/pendingRepo';
import { ApiError, asyncHandler } from '../middleware/errorHandler';

export async function listSellers(_req: Request, res: Response) {
  const sellers = await sellersRepo.list();
  res.json({ sellers });
}

export async function upsertSeller(req: Request, res: Response) {
  const { id, walletAddressUrl, keyId, privateKeyPath } = req.body ?? {};
  if (!id || !walletAddressUrl || !keyId || !privateKeyPath) {
    return res.status(400).json({
      error: 'Required fields: id, walletAddressUrl, keyId, privateKeyPath'
    });
  }
  await sellersRepo.upsert({ id, walletAddressUrl, keyId, privateKeyPath });
  return res.status(201).json({ ok: true, id });
}

export async function startQuote(req: Request, res: Response) {
  try {
    const { offerId } = req.params;
    const { sellerId, buyerWalletAddressUrl, amount } = req.body ?? {};
    if (!offerId || !sellerId || !buyerWalletAddressUrl || !amount) {
      return res.status(400).json({
        error: 'Required: offerId (param), sellerId, buyerWalletAddressUrl, amount'
      });
    }
    const result = await startQuoteFlow({
      offerId,
      sellerId,
      buyerWalletAddressUrl,
      amount: String(amount)
    });
    // Return enhanced response with all payment details
    return res.status(200).json({
      success: result.success || true,
      redirectUrl: result.redirectUrl,
      paymentUrl: result.paymentUrl || result.redirectUrl,
      pendingId: result.pendingId,
      incomingPaymentId: result.incomingPaymentId,
      quoteId: result.quoteId,
      amount: result.amount,
      assetCode: result.assetCode
    });
  } catch (err: any) {
    // eslint-disable-next-line no-console
    console.error('[startQuote] error', err);
    return res.status(500).json({ error: err?.message ?? 'internal_error' });
  }
}

export async function finishPayment(req: Request, res: Response) {
  try {
    const { pendingId, interact_ref, hash } = req.query as Record<string, string>;
    if (!pendingId || !interact_ref || !hash) {
      return res.status(400).json({ error: 'Required: pendingId, interact_ref, hash' });
    }
    const op = await completePayment({
      pendingId,
      interactRef: interact_ref,
      receivedHash: hash
    });
    return res.status(200).json({ ok: true, outgoingPayment: op });
  } catch (err: any) {
    // eslint-disable-next-line no-console
    console.error('[finishPayment] error', err);
    return res.status(500).json({ error: err?.message ?? 'internal_error' });
  }
}

export const getPaymentStatus = asyncHandler(async (req: Request, res: Response) => {
  const { pendingId } = req.params;
  
  const pending = await pendingRepo.get(pendingId);
  if (!pending) {
    throw new ApiError('Payment not found', 404);
  }
  
  return res.json({
    pendingId: pending.id,
    offerId: pending.offerId,
    status: pending.status,
    buyerWalletAddressUrl: pending.buyerWalletAddressUrl,
    incomingPaymentId: pending.incomingPaymentId,
    outgoingPaymentId: pending.outgoingPaymentId,
    quoteId: pending.quoteId
  });
});

export const listPendingPayments = asyncHandler(async (_req: Request, res: Response) => {
  const payments = await pendingRepo.list();
  return res.json({ 
    payments: payments.map(p => ({
      pendingId: p.id,
      offerId: p.offerId,
      status: p.status,
      buyerWalletAddressUrl: p.buyerWalletAddressUrl,
      incomingPaymentId: p.incomingPaymentId,
      outgoingPaymentId: p.outgoingPaymentId
    }))
  });
});

export const getOfferPayments = asyncHandler(async (req: Request, res: Response) => {
  const { offerId } = req.params;
  const payments = await pendingRepo.findByOfferId(offerId);
  
  return res.json({ 
    offerId,
    payments: payments.map(p => ({
      pendingId: p.id,
      status: p.status,
      buyerWalletAddressUrl: p.buyerWalletAddressUrl,
      incomingPaymentId: p.incomingPaymentId,
      outgoingPaymentId: p.outgoingPaymentId,
      quoteId: p.quoteId
    }))
  });
});

export const createIncomingPayment = asyncHandler(async (req: Request, res: Response) => {
  const { amount, description, sellerId } = req.body;
  
  if (!amount) {
    throw new ApiError('Required field: amount', 400);
  }
  
  // Use default seller if not specified
  const sellerIdToUse = sellerId || process.env.SELLER_ID || 'default-seller';
  
  const result = await createIncomingPaymentForJob({
    amount: String(amount),
    description: description || 'Job funding',
    sellerId: sellerIdToUse
  });
  
  return res.json({
    success: true,
    paymentId: result.incomingPaymentId,
    payment_id: result.incomingPaymentId, // Alternative key for compatibility
    data: result
  });
});

export const getWalletProfile = asyncHandler(async (req: Request, res: Response) => {
  const { walletAddressUrl } = req.body;
  
  if (!walletAddressUrl) {
    throw new ApiError('Required field: walletAddressUrl', 400);
  }
  
  // Import the getWalletDoc function
  const { getWalletDoc, buildSellerClient } = await import('../workflow/openPayments');
  
  // Get the first seller to use as authentication context
  const sellers = await sellersRepo.list();
  if (sellers.length === 0) {
    throw new ApiError('No seller configured', 500);
  }
  
  const seller = sellers[0];
  const client = await buildSellerClient({
    walletAddressUrl: seller.walletAddressUrl,
    keyId: seller.keyId,
    privateKeyPath: seller.privateKeyPath
  });
  
  const walletDoc = await getWalletDoc(client, walletAddressUrl);
  
  return res.json({
    success: true,
    wallet: walletDoc
  });
});


