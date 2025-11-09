// $ilp.interledger-test.dev/mvr5656 -> Emisor
// $ilp.interledger-test.dev/edutest -> Remitente
// $ilp.interledger-test.dev/bobtest5656 -> Receptor

import { createAuthenticatedClient } from '@interledger/open-payments';
import fs from 'fs';

// --- Wallets (ordenado por rol) ---
// Emisor: quién firma las solicitudes (normalmente tu cuenta vendedora)
// Remitente: comprador/cliente (no requiere llave privada aquí)
// Receptor: cuenta que recibe (si distinta del emisor)
const wallets = {
  emisor: {
    walletAddressUrl: 'https://ilp.interledger-test.dev/mvr5656',
    keyId: 'fe775339-6ebc-4eb8-a4b4-0811acba3b62',
    privateKeyPath: './privates/mvr5656.key'
  },
  remitente: {
    walletAddressUrl: 'https://ilp.interledger-test.dev/edutest',
    keyId: '01b21220-5331-47d2-bad9-25182dc9baf8',
    privateKeyPath: './privates/edutest.key'
  },
  receptor: {
    walletAddressUrl: 'https://ilp.interledger-test.dev/bobtest5656',
    keyId: '4005843b-a5fa-4b8a-b8aa-562b2b1326f3',
    privateKeyPath: './privates/bobtest5656.key'
  }
};

function loadPrivateKey(path) {
  return fs.readFileSync(path, 'utf8');
}

async function createClientFrom(wallet) {
  const privateKey = loadPrivateKey(wallet.privateKeyPath);
  return await createAuthenticatedClient({
    walletAddressUrl: wallet.walletAddressUrl,
    privateKey,
    keyId: wallet.keyId
  });
}

async function main() {
  // Autenticamos como Emisor (vendedor) para hacer solicitudes firmadas
  const client = await createClientFrom(wallets.emisor);

  // Leer direcciones públicas (no requieren autenticación del propietario)
  const sendingWalletAddress = await client.walletAddress.get({
    url: wallets.remitente.walletAddressUrl
  });

  const receivingWalletAddress = await client.walletAddress.get({
    url: wallets.receptor.walletAddressUrl
  });

  console.log('Sender:', sendingWalletAddress.id);
  console.log('Receiver:', receivingWalletAddress.id);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
