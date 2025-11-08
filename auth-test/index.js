// PASO 1: Importar las librerías correctas
import { createAuthenticatedClient } from '@interledger/open-payments';
import fs from 'fs';

// --- CONFIGURACIÓN ---

// Wallet Address de tu marketplace
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

    // PASO 1: Obtener información de la Wallet Address (GET wallet address)
    console.log('Obteniendo información de la wallet...');
    const walletAddress = await client.walletAddress.get({
      url: WALLET_ADDRESS
    });

    console.log('✅ Wallet Address obtenida!\n');
    console.log('  - ID:', walletAddress.id);
    console.log('  - Asset Code:', walletAddress.assetCode);
    console.log('  - Asset Scale:', walletAddress.assetScale);
    console.log('  - Auth Server:', walletAddress.authServer);
    console.log('  - Resource Server:', walletAddress.resourceServer);

    // PASO 2: Crear Incoming Payment usando la info de la wallet
    console.log('\nCreando un Incoming Payment de prueba...\n');

    const incomingPayment = await client.incomingPayment.create(
      {
        url: walletAddress.id, // URL del wallet address
      },
      {
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