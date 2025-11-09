import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import morgan from 'morgan';
import paymentsRouter from './web/routes';
import { errorHandler } from './middleware/errorHandler';

const app = express();

app.use(helmet());
app.use(cors());
app.use(express.json());
app.use(morgan('dev'));

app.get('/health', (_req, res) => {
  res.json({ status: 'ok', service: 'payments', time: new Date().toISOString() });
});

app.use('/', paymentsRouter);

// Error handler must be last
app.use(errorHandler);

export default app;


