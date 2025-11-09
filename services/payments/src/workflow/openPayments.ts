import fs from 'fs';
import { createAuthenticatedClient, isFinalizedGrant } from '@interledger/open-payments';

export type WalletDoc = {
  id: string;
  assetCode: string;
  assetScale: number;
  authServer: string;
  resourceServer: string;
};

export async function buildSellerClient(opts: { walletAddressUrl: string; keyId: string; privateKeyPath: string }) {
  const privateKey = fs.readFileSync(opts.privateKeyPath, 'utf8');
  const client = await createAuthenticatedClient({
    walletAddressUrl: opts.walletAddressUrl,
    privateKey,
    keyId: opts.keyId
  });
  return client;
}

export async function getWalletDoc(client: any, walletAddressUrl: string): Promise<WalletDoc> {
  const doc = await client.walletAddress.get({ url: walletAddressUrl });
  return {
    id: doc.id,
    assetCode: doc.assetCode,
    assetScale: doc.assetScale,
    authServer: doc.authServer,
    resourceServer: doc.resourceServer
  };
}

export async function requestIncomingPaymentGrant(client: any, authServer: string) {
  const grant = await client.grant.request({ url: authServer }, {
    access_token: {
      access: [{ type: 'incoming-payment', actions: ['create', 'read', 'read-all', 'complete', 'list'] }]
    }
  });
  if (!isFinalizedGrant(grant)) throw new Error('incoming-payment grant not finalized');
  return grant.access_token.value as string;
}

export async function createIncomingPayment(client: any, resourceServer: string, accessToken: string, args: {
  walletAddress: string;
  value: string;
  assetCode: string;
  assetScale: number;
  description?: string;
}) {
  return client.incomingPayment.create({ url: resourceServer, accessToken }, {
    walletAddress: args.walletAddress,
    incomingAmount: { value: args.value, assetCode: args.assetCode, assetScale: args.assetScale },
    ...(args.description && { metadata: { description: args.description } })
  });
}

export async function requestQuoteGrant(client: any, authServer: string) {
  const grant = await client.grant.request({ url: authServer }, {
    access_token: { access: [{ type: 'quote', actions: ['create', 'read', 'read-all'] }] }
  });
  if (!isFinalizedGrant(grant)) throw new Error('quote grant not finalized');
  return grant.access_token.value as string;
}

export async function createQuote(client: any, resourceServer: string, accessToken: string, args: {
  walletAddress: string;
  receiver: string;
}) {
  // Some SDK versions expose quote.create on "quote" not "quotes"
  if (!client.quote?.create) throw new Error('client.quote.create not available in SDK version');
  return client.quote.create({ url: resourceServer, accessToken }, {
    walletAddress: args.walletAddress,
    receiver: args.receiver,
    method: 'ilp'
  });
}

export async function requestInteractiveOutgoingGrant(client: any, authServer: string, args: {
  buyerWalletAddressUrl: string;
  debitAmount: { value: string; assetCode: string; assetScale: number };
  finish?: { uri: string; nonce: string }; // Optional for local testing
  clientId: string; // seller wallet id
}) {
  // Build interact object - finish is optional for local testing
  const interact: any = {
    start: ['redirect']
  };
  if (args.finish) {
    interact.finish = { method: 'redirect', uri: args.finish.uri, nonce: args.finish.nonce };
  }
  
  const grant = await client.grant.request({ url: authServer }, {
    access_token: {
      access: [{
        identifier: args.buyerWalletAddressUrl,
        type: 'outgoing-payment',
        actions: ['create', 'read', 'read-all', 'list', 'list-all'],
        limits: { debitAmount: args.debitAmount }
      }]
    },
    client: args.clientId,
    interact
  });
  
  // Debug: log the grant structure
  console.log('[requestInteractiveOutgoingGrant] grant response:', JSON.stringify(grant, null, 2));
  
  // Check for required fields (note: field is 'continue', not 'cont')
  // interact.finish is optional if we didn't provide finish in the request
  if (!grant?.interact?.redirect || !grant?.continue?.access_token?.value || !grant?.continue?.uri) {
    console.error('[requestInteractiveOutgoingGrant] missing fields. Grant:', grant);
    throw new Error('interactive grant response missing fields');
  }
  return {
    redirect: grant.interact.redirect as string,
    finishId: grant.interact?.finish as string,
    continueAccessToken: grant.continue.access_token.value as string,
    continueUri: grant.continue.uri as string
  };
}

export async function continueGrant(client: any, args: { continueUri: string; accessToken: string; interactRef: string }) {
  const cont = await client.grant.continue(
    { url: args.continueUri, accessToken: args.accessToken },
    { interact_ref: args.interactRef }
  );
  if (!isFinalizedGrant(cont)) throw new Error('continuation grant not finalized');
  return cont.access_token.value as string;
}

export async function createOutgoingPayment(client: any, resourceServer: string, accessToken: string, args: {
  buyerWalletAddressUrl: string;
  quoteId: string;
}) {
  return client.outgoingPayment.create({ url: resourceServer, accessToken }, {
    walletAddress: args.buyerWalletAddressUrl,
    quoteId: args.quoteId,
    metadata: {}
  });
}


