import dotenv from 'dotenv';
import http from 'http';
import app from './server';
import { sellersRepo } from './workbench/sellersRepo';

dotenv.config();

const PORT = process.env.PORT ? parseInt(process.env.PORT, 10) : 4001;

const server = http.createServer(app);

server.listen(PORT, () => {
  // eslint-disable-next-line no-console
  console.log(`[payments] listening on http://localhost:${PORT}`);
});

// Optional bootstrap: register default seller from env
// SELLER_ID, SELLER_WALLET_ADDRESS_URL, SELLER_KEY_ID, SELLER_PRIVATE_KEY_PATH
(async () => {
  const id = process.env.SELLER_ID;
  const walletAddressUrl = process.env.SELLER_WALLET_ADDRESS_URL;
  const keyId = process.env.SELLER_KEY_ID;
  const privateKeyPath = process.env.SELLER_PRIVATE_KEY_PATH;
  if (id && walletAddressUrl && keyId && privateKeyPath) {
    try {
      await sellersRepo.upsert({ id, walletAddressUrl, keyId, privateKeyPath });
      // eslint-disable-next-line no-console
      console.log(`[payments] seller bootstrap upserted: ${id}`);
    } catch (err) {
      // eslint-disable-next-line no-console
      console.error('[payments] failed to upsert seller from env', err);
    }
  } else {
    // eslint-disable-next-line no-console
    console.log('[payments] seller bootstrap skipped (missing SELLER_* env vars)');
  }
})();


