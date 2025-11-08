// PASO 1: Importar las librerías correctas
import { createAuthenticatedClient } from '@interledger/open-payments';
import fs from 'fs';

// --- CONFIGURACIÓN ---

// Wallet Address de tu marketplace (formato URL para el SDK)
// Payment Pointer (para compartir): $ilp.interledger-test.dev/aicdmx
const WALLET_ADDRESS = 'https://ilp.interledger-test.dev/aicdmx';

// Key ID de tu llave (el que aparece en la UI de Rafiki)
const KEY_ID = 'd405beb8-f84a-4449-b989-93d0c7e38f02';

// Archivo de tu llave privada
const PRIVATE_KEY_FILE = './private.key';

// --- FIN DE LA CONFIGURACIÓN ---

async function getAccessToken() {
  console.log('Iniciando cliente de autenticación...');

  let privateKey;
  try {
    // Lee tu llave privada del archivo (formato PEM)
    privateKey = fs.readFileSync(PRIVATE_KEY_FILE, 'utf8');
    console.log('Llave privada cargada exitosamente.');
  } catch (err) {
    console.error(`\n❌ ERROR: No se pudo leer el archivo ${PRIVATE_KEY_FILE}.`);
    console.error('Asegúrate de que el archivo exista y el nombre sea correcto.');
    return; // Detiene la ejecución si no hay llave
  }

  try {
    // Crea el cliente autenticado
    const client = await createAuthenticatedClient({
      walletAddressUrl: WALLET_ADDRESS,
      privateKey: privateKey,
      keyId: KEY_ID
    });

    console.log('✅ Cliente autenticado creado exitosamente!\n');

    // PASO 1: Usar información conocida de la Wallet Address
    // (obtenida previamente con curl, el servidor es lento para el SDK)
    console.log('Usando información de la wallet...');
    const walletAddress = {
      id: 'https://ilp.interledger-test.dev/aicdmx',
      publicName: 'ai_cdmx',
      assetCode: 'MXN',
      assetScale: 2,
      authServer: 'https://auth.interledger-test.dev/f537937b-7016-481b-b655-9f0d1014822c',
      resourceServer: 'https://ilp.interledger-test.dev/f537937b-7016-481b-b655-9f0d1014822c'
    };

    console.log('✅ Wallet Address configurada!\n');
    console.log('  - ID:', walletAddress.id);
    console.log('  - Asset Code:', walletAddress.assetCode);
    console.log('  - Asset Scale:', walletAddress.assetScale);
    console.log('  - Auth Server:', walletAddress.authServer);
    console.log('  - Resource Server:', walletAddress.resourceServer);

    // PASO 2: Solicitar Grant (permiso) para crear Incoming Payment
    console.log('\nSolicitando grant para crear Incoming Payment...\n');

    const incomingPaymentGrant = await client.grant.request(
      {
        url: walletAddress.authServer
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
      },
    );

    console.log('✅ Grant obtenido!\n');
    console.log('Access Token:', incomingPaymentGrant.access_token.value.substring(0, 50) + '...');

    // PASO 3: Crear Incoming Payment usando el access token
    console.log('\nCreando un Incoming Payment de prueba...\n');

    const incomingPayment = await client.incomingPayment.create(
      {
        url: walletAddress.resourceServer, // URL del Resource Server
        accessToken: incomingPaymentGrant.access_token.value // Access token del grant
      },
      {
        walletAddress: walletAddress.id, // ID del wallet address
        incomingAmount: {
          value: '100', // 1 MXN (100 centavos porque assetScale es 2)
          assetCode: walletAddress.assetCode,
          assetScale: walletAddress.assetScale
        }
      }
    );

    console.log('✅ ¡INCOMING PAYMENT CREADO EXITOSAMENTE! ✅\n');
    console.log('ID del pago:', incomingPayment.id);
    console.log('Monto:', incomingPayment.incomingAmount);
    console.log('Wallet Address:', incomingPayment.walletAddress);
    console.log('\n🎉 La autenticación funciona correctamente! 🎉');

  } catch (error) {
    console.error('\n❌ ERROR ❌\n');
    console.error('Detalles del error:');
    console.error(error.message);
    if (error.description) {
      console.error('Descripción:', error.description);
    }
    console.error('\nStack trace completo:');
    console.error(error);
  }
}

// Ejecuta la función
getAccessToken();