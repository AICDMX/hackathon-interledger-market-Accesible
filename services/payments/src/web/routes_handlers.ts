import { Request, Response } from 'express';
import { startQuoteFlow, completePayment } from '../workflow/paymentsService';
import { sellersRepo } from '../workbench/sellersRepo';

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
    return res.status(200).json(result);
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


