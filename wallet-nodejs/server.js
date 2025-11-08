// Express Server - Payments Service
// Microservicio Node.js para manejar Open Payments API

import express from 'express';
import cors from 'cors';
import dotenv from 'dotenv';
import paymentRoutes from './src/routes/payments.js';

// Cargar variables de entorno
dotenv.config();

// Crear app de Express
const app = express();
const PORT = process.env.PORT || 3001;

// Middleware
app.use(cors()); // Permitir CORS para que Django pueda llamar a este servicio
app.use(express.json()); // Parsear JSON en el body de las requests
app.use(express.urlencoded({ extended: true }));

// Logger middleware
app.use((req, res, next) => {
  console.log(`\n📨 ${req.method} ${req.path}`);
  if (req.body && Object.keys(req.body).length > 0) {
    console.log('   Body:', JSON.stringify(req.body, null, 2));
  }
  next();
});

// Montar rutas
app.use('/', paymentRoutes);

// Ruta raíz
app.get('/', (req, res) => {
  res.json({
    service: 'Payments Service - Open Payments API Wrapper',
    version: '1.0.0',
    endpoints: {
      health: 'GET /health',
      createIncomingPayment: 'POST /api/payments/incoming',
      createOutgoingPayment: 'POST /api/payments/outgoing',
      webhook: 'POST /api/webhooks/payment-completed'
    },
    wallet: {
      address: process.env.WALLET_ADDRESS,
      assetCode: process.env.ASSET_CODE
    }
  });
});

// Manejo de errores 404
app.use((req, res) => {
  res.status(404).json({
    error: 'Endpoint no encontrado',
    path: req.path,
    method: req.method
  });
});

// Manejo de errores global
app.use((err, req, res, next) => {
  console.error('❌ Error en el servidor:', err);
  res.status(500).json({
    error: 'Error interno del servidor',
    message: err.message
  });
});

// Iniciar servidor
app.listen(PORT, () => {
  console.log('\n╔═══════════════════════════════════════════════════╗');
  console.log('║   🚀 PAYMENTS SERVICE - OPEN PAYMENTS API       ║');
  console.log('╚═══════════════════════════════════════════════════╝');
  console.log(`\n✅ Servidor corriendo en: http://localhost:${PORT}`);
  console.log(`✅ Wallet del Marketplace: ${process.env.WALLET_ADDRESS}`);
  console.log(`✅ Asset Code: ${process.env.ASSET_CODE}\n`);
  console.log('📋 Endpoints disponibles:');
  console.log(`   GET  http://localhost:${PORT}/health`);
  console.log(`   POST http://localhost:${PORT}/api/payments/incoming`);
  console.log(`   POST http://localhost:${PORT}/api/payments/outgoing`);
  console.log(`   POST http://localhost:${PORT}/api/webhooks/payment-completed`);
  console.log('\n💡 Presiona Ctrl+C para detener el servidor\n');
});
