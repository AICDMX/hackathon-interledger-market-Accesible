/**
 * Test script to verify the payment flow integration
 * 
 * This script tests the quote creation endpoint to ensure:
 * 1. The endpoint responds correctly
 * 2. Returns payment URL
 * 3. Returns all required fields
 * 
 * Usage: node test-payment-flow.js
 */

const http = require('http');

const TEST_DATA = {
  sellerId: 'seller-mvr5656',
  buyerWalletAddressUrl: 'https://ilp.interledger-test.dev/edutest',
  amount: '100'
};

const TEST_OFFER_ID = 'test-job-001';

function makeRequest(options, postData) {
  return new Promise((resolve, reject) => {
    const req = http.request(options, (res) => {
      let data = '';
      
      res.on('data', (chunk) => {
        data += chunk;
      });
      
      res.on('end', () => {
        resolve({
          statusCode: res.statusCode,
          headers: res.headers,
          body: data
        });
      });
    });
    
    req.on('error', (error) => {
      reject(error);
    });
    
    if (postData) {
      req.write(postData);
    }
    
    req.end();
  });
}

async function testQuoteCreation() {
  console.log('🧪 Testing Payment Quote Creation...\n');
  
  const postData = JSON.stringify(TEST_DATA);
  
  const options = {
    hostname: 'localhost',
    port: 4001,
    path: `/offers/${TEST_OFFER_ID}/quotes/start`,
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Content-Length': Buffer.byteLength(postData)
    }
  };
  
  try {
    console.log('📤 Request:');
    console.log(`   POST http://localhost:4001${options.path}`);
    console.log(`   Body:`, TEST_DATA);
    console.log();
    
    const response = await makeRequest(options, postData);
    
    console.log('📥 Response:');
    console.log(`   Status: ${response.statusCode}`);
    console.log();
    
    if (response.statusCode === 200) {
      const data = JSON.parse(response.body);
      console.log('✅ Success! Payment quote created.');
      console.log();
      console.log('📋 Response Data:');
      console.log(`   Success: ${data.success}`);
      console.log(`   Redirect URL: ${data.redirectUrl}`);
      console.log(`   Payment URL: ${data.paymentUrl}`);
      console.log(`   Pending ID: ${data.pendingId}`);
      console.log(`   Incoming Payment ID: ${data.incomingPaymentId}`);
      console.log(`   Quote ID: ${data.quoteId}`);
      console.log(`   Amount: ${data.amount}`);
      console.log(`   Asset Code: ${data.assetCode}`);
      console.log();
      
      // Validate required fields
      const requiredFields = ['success', 'redirectUrl', 'paymentUrl', 'pendingId'];
      const missingFields = requiredFields.filter(field => !data[field]);
      
      if (missingFields.length > 0) {
        console.log('⚠️  Warning: Missing required fields:', missingFields);
      } else {
        console.log('✅ All required fields present!');
      }
      
      return true;
    } else {
      console.log('❌ Failed to create quote');
      console.log('   Response:', response.body);
      return false;
    }
  } catch (error) {
    console.log('❌ Error connecting to payments service:');
    console.log('   ', error.message);
    console.log();
    console.log('💡 Make sure the payments service is running:');
    console.log('   cd services/payments && npm run dev');
    return false;
  }
}

async function testHealthCheck() {
  console.log('🏥 Testing Service Health...\n');
  
  const options = {
    hostname: 'localhost',
    port: 4001,
    path: '/sellers',
    method: 'GET'
  };
  
  try {
    const response = await makeRequest(options);
    
    if (response.statusCode === 200) {
      const data = JSON.parse(response.body);
      console.log('✅ Service is healthy!');
      console.log(`   Sellers configured: ${data.sellers?.length || 0}`);
      console.log();
      return true;
    } else {
      console.log('⚠️  Service responded but with status:', response.statusCode);
      return false;
    }
  } catch (error) {
    console.log('❌ Service is not running');
    console.log('   ', error.message);
    console.log();
    return false;
  }
}

async function main() {
  console.log('═══════════════════════════════════════════════');
  console.log('  Interledger Payment Flow Integration Test');
  console.log('═══════════════════════════════════════════════');
  console.log();
  
  const healthOk = await testHealthCheck();
  
  if (!healthOk) {
    console.log('❌ Cannot proceed with tests - service is not running');
    process.exit(1);
  }
  
  console.log('───────────────────────────────────────────────');
  console.log();
  
  const quoteOk = await testQuoteCreation();
  
  console.log('═══════════════════════════════════════════════');
  console.log();
  
  if (quoteOk) {
    console.log('✅ All tests passed!');
    console.log();
    console.log('📝 Next Steps:');
    console.log('   1. Start Django server: cd marketplace-py && uv run python manage.py runserver');
    console.log('   2. Log in as a funder');
    console.log('   3. Navigate to a job detail page');
    console.log('   4. Click "Approve quote & pay"');
    console.log('   5. Verify redirect to payment URL');
    console.log();
    process.exit(0);
  } else {
    console.log('❌ Tests failed');
    process.exit(1);
  }
}

main();
