// Payments Controller
// Lógica de negocio para manejar pagos con Open Payments API

import { getAuthenticatedClient, getWalletAddress } from '../services/openPaymentsClient.js';

/**
 * Crea un Incoming Payment (escrow)
 * POST /api/payments/incoming
 * Body: { amount: "100", description: "Escrow para Brief #123" }
 */
export async function createIncomingPayment(req, res) {
  try {
    const { amount, description } = req.body;

    if (!amount) {
      return res.status(400).json({
        success: false,
        error: 'El campo "amount" es requerido'
      });
    }

    console.log(`\n🔵 Creando Incoming Payment por $${amount}...`);

    // Obtener cliente autenticado
    const client = await getAuthenticatedClient();
    const walletAddress = getWalletAddress();

    // PASO 1: Solicitar grant para crear incoming payment
    console.log('  → Solicitando grant...');
    const incomingPaymentGrant = await client.grant.request(
      { url: walletAddress.authServer },
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

    console.log('  → Grant obtenido ✅');

    // PASO 2: Crear incoming payment con el access token
    console.log('  → Creando incoming payment...');
    const incomingPayment = await client.incomingPayment.create(
      {
        url: walletAddress.resourceServer,
        accessToken: incomingPaymentGrant.access_token.value
      },
      {
        walletAddress: walletAddress.id,
        incomingAmount: {
          value: amount,
          assetCode: walletAddress.assetCode,
          assetScale: walletAddress.assetScale
        },
        metadata: {
          description: description || 'Payment to marketplace'
        }
      }
    );

    console.log('✅ Incoming Payment creado exitosamente!');
    console.log('  - Payment ID:', incomingPayment.id);
    console.log('  - Amount:', incomingPayment.incomingAmount);

    // Retornar respuesta exitosa
    return res.status(200).json({
      success: true,
      paymentId: incomingPayment.id,
      paymentUrl: incomingPayment.id, // Este es el URL que el funder debe pagar
      incomingAmount: incomingPayment.incomingAmount,
      walletAddress: incomingPayment.walletAddress,
      metadata: incomingPayment.metadata
    });

  } catch (error) {
    console.error('❌ Error al crear incoming payment:', error.message);
    return res.status(500).json({
      success: false,
      error: error.message,
      description: error.description || 'Error desconocido'
    });
  }
}

/**
 * Crea un Outgoing Payment (liberar pago al creator)
 * POST /api/payments/outgoing
 * Body: { receiverWalletAddress: "$ilp.../creator", amount: "100", description: "Pago a creator" }
 */
export async function createOutgoingPayment(req, res) {
  try {
    const { incomingPaymentUrl, amount, description } = req.body;

    if (!incomingPaymentUrl || !amount) {
      return res.status(400).json({
        success: false,
        error: 'Los campos "incomingPaymentUrl" y "amount" son requeridos'
      });
    }

    console.log(`\n🔵 Creando Outgoing Payment de $${amount} para ${incomingPaymentUrl}...`);

    // Obtener cliente autenticado
    const client = await getAuthenticatedClient();
    const walletAddress = getWalletAddress();

    // PASO 1: Solicitar grant para outgoing payment
    console.log('  → Solicitando grant para outgoing payment...');
    const outgoingPaymentGrant = await client.grant.request(
      { url: walletAddress.authServer },
      {
        access_token: {
          access: [
            {
              identifier: walletAddress.id,
              type: 'outgoing-payment',
              actions: ['create', 'read'],
              limits: {
                  debitAmount: {
                      value: amount,
                      assetCode: walletAddress.assetCode,
                      assetScale: walletAddress.assetScale
                  }
              }
            }
          ]
        },
        interact: {
            start: ['redirect'],
            finish: {
                method: 'redirect',
                uri: 'http://localhost:3001/callback', // Placeholder callback URL
                nonce: 'some-random-nonce' // Placeholder nonce
            }
        }
      }
    );

    console.log('  → Outgoing payment grant obtenido ✅');

    // PASO 2: Crear Outgoing Payment directamente (sin quote manual)
    console.log('  → Creando outgoing payment directamente...');
    const outgoingPayment = await client.outgoingPayment.create(
      {
        url: walletAddress.resourceServer,
        accessToken: outgoingPaymentGrant.access_token.value
      },
      {
        walletAddress: walletAddress.id,
        incomingPayment: incomingPaymentUrl,
        debitAmount: {
          value: amount,
          assetCode: walletAddress.assetCode,
          assetScale: walletAddress.assetScale
        },
        metadata: {
          description: description || 'Payment from marketplace'
        }
      }
    );

    console.log('✅ Outgoing Payment creado exitosamente!');
    console.log('  - Payment ID:', outgoingPayment.id);
    console.log('  - Sent Amount:', outgoingPayment.sentAmount);
    console.log('  - Incoming Payment URL:', outgoingPayment.incomingPayment);

    // Retornar respuesta exitosa
    return res.status(200).json({
      success: true,
      paymentId: outgoingPayment.id,
      sentAmount: outgoingPayment.sentAmount,
      incomingPayment: outgoingPayment.incomingPayment,
      metadata: outgoingPayment.metadata
    });

  } catch (error) {
    console.error('❌ Error al crear outgoing payment:', error.message);
    console.error('📋 Error completo:', JSON.stringify(error, null, 2));
    if (error.description) console.error('📝 Descripción:', error.description);
    if (error.validationErrors) console.error('⚠️  Validation Errors:', JSON.stringify(error.validationErrors, null, 2));

    return res.status(500).json({
      success: false,
      error: error.message,
      description: error.description || 'Error desconocido',
      validationErrors: error.validationErrors || null
    });
  }
}

/**
 * Health check endpoint
 * GET /health
 */
export function healthCheck(req, res) {
  return res.status(200).json({
    status: 'ok',
    service: 'payments-service',
    timestamp: new Date().toISOString(),
    wallet: {
      address: process.env.WALLET_ADDRESS,
      assetCode: process.env.ASSET_CODE
    }
  });
}

/**
 * Webhook para recibir notificaciones de pagos completados
 * POST /api/webhooks/payment-completed
 */
export function paymentWebhook(req, res) {
  try {
    console.log('\n🔔 Webhook recibido:', req.body);

    // TODO: Implementar validación del webhook
    // TODO: Notificar a Django cuando un pago se complete

    return res.status(200).json({
      received: true,
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    console.error('❌ Error en webhook:', error.message);
    return res.status(500).json({
      success: false,
      error: error.message
    });
  }
}
