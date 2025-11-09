import fs from 'fs';
import path from 'path';

export type SellerRecord = {
  id: string;
  walletAddressUrl: string;
  keyId: string;
  privateKeyPath: string; // local filesystem path to PEM/PKCS8 private key
};

type SellersDb = { sellers: SellerRecord[] };

const DATA_DIR = path.join(__dirname, '..', '..', 'data');
const SELLERS_PATH = path.join(DATA_DIR, 'sellers.json');

function ensureDataDir() {
  if (!fs.existsSync(DATA_DIR)) fs.mkdirSync(DATA_DIR, { recursive: true });
  if (!fs.existsSync(SELLERS_PATH)) fs.writeFileSync(SELLERS_PATH, JSON.stringify({ sellers: [] }, null, 2));
}

function readDb(): SellersDb {
  ensureDataDir();
  const raw = fs.readFileSync(SELLERS_PATH, 'utf8');
  return JSON.parse(raw) as SellersDb;
}

function writeDb(db: SellersDb) {
  ensureDataDir();
  fs.writeFileSync(SELLERS_PATH, JSON.stringify(db, null, 2));
}

async function list(): Promise<SellerRecord[]> {
  const db = readDb();
  return db.sellers;
}

async function get(id: string): Promise<SellerRecord | undefined> {
  const db = readDb();
  return db.sellers.find((s) => s.id === id);
}

async function upsert(record: SellerRecord): Promise<void> {
  const db = readDb();
  const idx = db.sellers.findIndex((s) => s.id === record.id);
  if (idx >= 0) {
    db.sellers[idx] = record;
  } else {
    db.sellers.push(record);
  }
  writeDb(db);
}

export const sellersRepo = { list, get, upsert };


