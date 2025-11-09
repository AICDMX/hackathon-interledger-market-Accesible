import fs from 'fs';
import path from 'path';

export type PendingPaymentRecord = {
  id: string; // ULID
  offerId: string;
  sellerId: string;
  buyerWalletAddressUrl: string;
  // created during start
  incomingPaymentId?: string;
  quoteId?: string;
  interactRedirect?: string;
  finishId?: string;
  continueAccessToken?: string;
  continueUri?: string;
  // hydration
  buyer?: {
    id: string; // wallet address URL
    authServer: string;
    resourceServer: string;
  };
  status: 'pending' | 'paid' | 'failed';
  outgoingPaymentId?: string;
};

type PendingDb = { pendings: PendingPaymentRecord[] };

const DATA_DIR = path.join(__dirname, '..', '..', 'data');
const PENDING_PATH = path.join(DATA_DIR, 'pending.json');

function ensureDataDir() {
  if (!fs.existsSync(DATA_DIR)) fs.mkdirSync(DATA_DIR, { recursive: true });
  if (!fs.existsSync(PENDING_PATH)) fs.writeFileSync(PENDING_PATH, JSON.stringify({ pendings: [] }, null, 2));
}

function readDb(): PendingDb {
  ensureDataDir();
  const raw = fs.readFileSync(PENDING_PATH, 'utf8');
  return JSON.parse(raw) as PendingDb;
}

function writeDb(db: PendingDb) {
  ensureDataDir();
  fs.writeFileSync(PENDING_PATH, JSON.stringify(db, null, 2));
}

async function create(rec: PendingPaymentRecord): Promise<void> {
  const db = readDb();
  db.pendings.push(rec);
  writeDb(db);
}

async function update(id: string, patch: Partial<PendingPaymentRecord>): Promise<PendingPaymentRecord | undefined> {
  const db = readDb();
  const idx = db.pendings.findIndex((p) => p.id === id);
  if (idx < 0) return undefined;
  const updated = { ...db.pendings[idx], ...patch };
  db.pendings[idx] = updated;
  writeDb(db);
  return updated;
}

async function get(id: string): Promise<PendingPaymentRecord | undefined> {
  const db = readDb();
  return db.pendings.find((p) => p.id === id);
}

async function list(): Promise<PendingPaymentRecord[]> {
  const db = readDb();
  return db.pendings;
}

async function findByOfferId(offerId: string): Promise<PendingPaymentRecord[]> {
  const db = readDb();
  return db.pendings.filter((p) => p.offerId === offerId);
}

export const pendingRepo = { create, update, get, list, findByOfferId };


