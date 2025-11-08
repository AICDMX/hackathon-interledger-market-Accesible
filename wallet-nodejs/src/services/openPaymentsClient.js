// Open Payments Client Service
// Maneja la autenticación y comunicación con Open Payments API

import { createAuthenticatedClient } from '@interledger/open-payments';
import fs from 'fs';
import dotenv from 'dotenv';

// Cargar variables de entorno PRIMERO
dotenv.config();

/**
 * Retorna la información de la wallet del marketplace
 * (función en lugar de constante para asegurar que .env está cargado)
 */
export function getWalletAddress() {
  return {
    id: process.env.WALLET_ADDRESS,
    publicName: 'ai_cdmx',
    assetCode: process.env.ASSET_CODE,
    assetScale: parseInt(process.env.ASSET_SCALE),
    authServer: process.env.AUTH_SERVER,
    resourceServer: process.env.RESOURCE_SERVER
  };
}

/**
 * Crea y retorna un cliente autenticado de Open Payments
 */
export async function getAuthenticatedClient() {
  try {
    // Leer la private key del archivo
    const privateKey = fs.readFileSync(process.env.PRIVATE_KEY_PATH, 'utf8');

    // Crear el cliente autenticado
    const client = await createAuthenticatedClient({
      walletAddressUrl: process.env.WALLET_ADDRESS,
      privateKey: privateKey,
      keyId: process.env.KEY_ID
    });

    console.log('✅ Cliente de Open Payments autenticado exitosamente');
    return client;
  } catch (error) {
    console.error('❌ Error al crear cliente autenticado:', error.message);
    throw error;
  }
}
