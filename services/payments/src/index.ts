import dotenv from 'dotenv';
import http from 'http';
import app from './server';

dotenv.config();

const PORT = process.env.PORT ? parseInt(process.env.PORT, 10) : 4001;

const server = http.createServer(app);

server.listen(PORT, () => {
  // eslint-disable-next-line no-console
  console.log(`[payments] listening on http://localhost:${PORT}`);
});


