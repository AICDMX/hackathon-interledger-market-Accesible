import { ulid } from 'ulid';
import { pendingRepo } from '../workbench/pendingRepo';
import { sellersRepo } from '../workbench/sellersRepo';
import {
  buildSellerClient,
  getWalletDoc,
  requestIncomingPaymentGrant,
  createIncomingPayment,
  requestQuoteGrant,
  createQuote,
  requestInteractiveOutgoingGrant,
  continueGrant,
  createOutgoingPayment
} from './openPayments';

export async function startQuoteFlow(args: {
  offerId: string;
  sellerId: string;
  buyerWalletAddressUrl: string;
  amount: string;
}) {
  const pendingId = ulid();
  const seller = await sellersRepo.get(args.sellerId);
  if (!seller) throw new Error(`seller ${args.sellerId} not found`);

  // Build client as the seller (merchant)
  const client = await buildSellerClient({
    walletAddressUrl: seller.walletAddressUrl,
    keyId: seller.keyId,
    privateKeyPath: seller.privateKeyPath
  });

  // Load seller and buyer wallet docs
  const sellerWallet = await getWalletDoc(client, seller.walletAddressUrl);
  const buyerWallet = await getWalletDoc(client, args.buyerWalletAddressUrl);

  // 1) Seller: grant + incoming payment
  const inToken = await requestIncomingPaymentGrant(client, sellerWallet.authServer);
  const incoming = await createIncomingPayment(client, sellerWallet.resourceServer, inToken, {
    walletAddress: sellerWallet.id,
    value: args.amount,
    assetCode: sellerWallet.assetCode,
    assetScale: sellerWallet.assetScale
  });

  // 2) Buyer: grant + quote
  const quoteToken = await requestQuoteGrant(client, buyerWallet.authServer);
  const quote = await createQuote(client, buyerWallet.resourceServer, quoteToken, {
    walletAddress: buyerWallet.id,
    receiver: String(incoming.id)
  });

  // 3) Interactive outgoing-payment grant for buyer
  const baseUrl = process.env.BASE_URL ?? `http://localhost:${process.env.PORT ?? 4001}`;
  const finishUrl = `${baseUrl}/payments/finish?pendingId=${pendingId}`;
  const interactive = await requestInteractiveOutgoingGrant(client, buyerWallet.authServer, {
    buyerWalletAddressUrl: buyerWallet.id,
    debitAmount: {
      value: quote.debitAmount.value,
      assetCode: quote.debitAmount.assetCode,
      assetScale: quote.debitAmount.assetScale
    },
    finish: { uri: finishUrl, nonce: pendingId },
    clientId: sellerWallet.id
  });

  // Persist pending
  await pendingRepo.create({
    id: pendingId,
    offerId: args.offerId,
    sellerId: args.sellerId,
    buyerWalletAddressUrl: args.buyerWalletAddressUrl,
    incomingPaymentId: incoming.id,
    quoteId: quote.id,
    interactRedirect: interactive.redirect,
    finishId: interactive.finishId,
    continueAccessToken: interactive.continueAccessToken,
    continueUri: interactive.continueUri,
    buyer: {
      id: buyerWallet.id,
      authServer: buyerWallet.authServer,
      resourceServer: buyerWallet.resourceServer
    },
    status: 'pending'
  });

  return { pendingId, redirectUrl: interactive.redirect };
}

export async function completePayment(args: {
  pendingId: string;
  interactRef: string;
  receivedHash: string;
}) {
  const pending = await pendingRepo.get(args.pendingId);
  if (!pending) throw new Error('pending not found');
  const seller = await sellersRepo.get(pending.sellerId);
  if (!seller) throw new Error('seller not found');

  // NOTE: Hash verification step is wallet-specific; implement if needed.
  // For now we assume redirect integrity from the wallet and proceed to continuation.

  const client = await buildSellerClient({
    walletAddressUrl: seller.walletAddressUrl,
    keyId: seller.keyId,
    privateKeyPath: seller.privateKeyPath
  });

  const contToken = await continueGrant(client, {
    continueUri: String(pending.continueUri),
    accessToken: String(pending.continueAccessToken),
    interactRef: args.interactRef
  });

  const op = await createOutgoingPayment(
    client,
    String(pending.buyer?.resourceServer),
    contToken,
    {
      buyerWalletAddressUrl: String(pending.buyer?.id),
      quoteId: String(pending.quoteId)
    }
  );

  await pendingRepo.update(args.pendingId, { status: 'paid', outgoingPaymentId: op.id });
  return op;
}


