// $ilp.interledger-test.dev/mvr5656 -> Emisor

// $ilp.interledger-test.dev/edutest -> Remitente

// $ilp.interledger-test.dev/bobtest5656 -> Receptor

import { createAuthenticatedClient, isFinalizedGrant } from '@interledger/open-payments';
import fs from 'fs';

(async () => {
  const privateKey = fs.readFileSync('./private.key', 'utf8');
  const client = await createAuthenticatedClient({
    walletAddressUrl: 'https://ilp.interledger-test.dev/mvr5656',
    privateKey: privateKey,
    keyId: 'fe775339-6ebc-4eb8-a4b4-0811acba3b62'
  });

})();

const sendindWalletAddress = await client.walletAddress.get( {
    url: 'https://ilp.interledger-test.dev/edutest'
});

const receivingWalletAddress = await client.walletAddress.get( {
    url: 'https://ilp.interledger-test.dev/bobtest5656'
});

console.log(sendindWalletAddress, receivingWalletAddress);

const incomingPaymentGrant = await client.grant.request( 
    {
        url: receivingWalletAddress.authServer,
    },
    {
        access_token: {
            access: [
                {
                    type: 'incoming-payment',
                    actions: ['create'],
                },
            ],
        },
    }
);

if (!isFinalizedGrant(incomingPaymentGrant)) {
    throw new Error('Grant not finalized');
}

