# Open Payments CRUD overview

This document explains how the backend CRUD layer talks to the [Open Payments](https://openpayments.dev) API. The code in `backend/app/app/crud/openpayments` wraps the in-house Open Payments SDK and exposes a single high-level helper (`OpenPaymentsProcessor`) that orchestrates every step of the interoperable grant + payment flow.

## Key components

- `OpenPaymentsProcessor` (`backend/app/app/crud/openpayments/crud_open_payments.py`)  
  Encapsulates the entire sequence defined in the Open Payments reference flow – requesting grants, creating incoming payments, acquiring quotes, driving the interactive authorization, and finally creating the outgoing payment once the buyer finishes the interaction.
- Open Payments SDK (`backend/app/app/open_payments_sdk/…`)  
  A light client that knows how to talk to wallets, grant servers, and resource servers. The processor composes it with the seller's key pair and wallet address.
- Helper schemas (`backend/app/app/schemas/openpayments/open_payments.py`)  
  `SellerOpenPaymentAccount` normalizes seller credentials (wallet URL + private key) and `PendingIncomingPaymentTransaction` stores the temporary state required to resume an interactive payment after the browser round-trip.
- Utility helpers (`backend/app/app/utilities/openpayments.py`)  
  Normalize `$wallet` handles, encapsulate PEM handling, and verify the consent hash returned by an authorization server.
- FastAPI endpoint (`backend/app/app/api/api_v1/endpoints/openpayments.py`)  
  Shows how the processor is wired into HTTP handlers: `/order/{id}` prepares the payment and returns the redirect URL, `/fulfil/{key}` is intended to finalize the transfer.

The remaining CRUD modules inside `crud/openpayments` (`crud_order.py`, `crud_wallet.py`, etc.) simply subclass `CRUDBase` so the API can store Open Payments metadata in the database once that portion of the system is implemented.

## Processor lifecycle

1. **Initialization**  
   When created, the processor:
   - normalizes the buyer wallet URL (`paymentsparser.normalise_wallet_address`);
   - instantiates an `OpenPaymentsClient` using the seller's keyId/private key and wallet address;
   - fetches both wallet address documents through the SDK (`client.wallet.get_wallet_address`);
   - seeds a `PendingIncomingPaymentTransaction` with the seller/buyer wallet info and a ULID that doubles as the interaction nonce + tracking key; and
   - builds a redirect URI (`settings.DEFAULT_REDIRECT_AFTER_AUTH`) suffixed with the ULID so the frontend has a stable callback target.

2. **Grant utility (`request_grant`)**  
   A tiny method that wraps `client.grants.post_grant_request`. It accepts the grant `type`, the `actions` array, and the target auth server endpoint, returning a GNAP `Grant`. Every subsequent step reuses this helper.

3. **Seller incoming payment (`request_incoming_payment`)**  
   - Requests an `incoming-payment` grant against the seller's auth server (`seller_wallet.authServer`) with actions `create/read/read-all/complete/list`.  
   - Uses the returned access token to POST an `IncomingPaymentRequest` to the seller's resource server so funds can be reserved for the sale.

4. **Buyer quote (`request_quote`)**  
   - Requests a `quote` grant from the buyer's auth server.  
   - Posts a `QuoteRequest` (using the buyer wallet address as the `walletAddress` and the seller's incoming payment URL as the `receiver`) to the buyer's resource server. The resulting `Quote` provides the debit amount and asset scale needed for the interactive step.

5. **Interactive grant (`get_purchase_endpoint`)**  
   - Chains the two previous operations, persisting the `incoming_payment_id` and `quote_id` inside `self.pending_payment`.  
   - Builds a GNAP grant with `type: outgoing-payment`, scopes it to the buyer's wallet identifier, and constrains it to the quoted debit amount.  
   - Supplies `interact.start = ["redirect"]` and `interact.finish` metadata so the authorization server knows where to return the user and which nonce (`PendingIncomingPaymentTransaction.id`) to echo back.  
   - Calls `client.grants.post_grant_request` once more, this time against the buyer's auth server, and records the resulting redirect URL plus the continuation handles (`finish_id`, `continue_id`, `continue_url`).  
   - Returns the redirect URL to the caller so the browser can be sent to the buyer's wallet for approval.

6. **Completing the payment (`complete_payment`)**  
   - When the buyer finishes the interaction, their wallet calls back with `interact_ref` and `hash`. The hash is verified against the saved state via `paymentsparser.verify_response_hash` to prevent tampering.  
   - Uses `client.grants.post_grant_continuation_request` with the continuation URI and access token from step 5 to obtain a usable access token.  
   - Creates an `OutgoingPaymentRequest` bound to the original quote and POSTs it to the buyer's resource server, which debits the buyer and pays the seller.

Because `PendingIncomingPaymentTransaction` currently lives in memory, callers must persist it themselves between `get_purchase_endpoint` and `complete_payment` (e.g., in Redis keyed by `pending_payment.id`). The TODO in the code signals this requirement.

## API wiring

`backend/app/app/api/api_v1/endpoints/openpayments.py` demonstrates the expected control flow:

1. `/order/{id}` receives an item ID, quantity, and the buyer wallet URL. It loads the seller credentials from configuration (`settings.TEST_SELLER_*`), instantiates `OpenPaymentsProcessor`, and sequentially calls `request_incoming_payment`, `request_quote`, and `get_purchase_endpoint`. The final redirect URL is returned to the frontend.
2. `/fulfil/{key}` is intended to run after the buyer approves the payment. Once storage for `PendingIncomingPaymentTransaction` is in place, this route will look up the pending state by `key`, then call `complete_payment(interact_ref, hash, pending_payment)` to submit the outgoing payment.

## Extending the flow

- **Persist pending transactions**  
  Replace the in-memory `self.pending_payment` with records stored via SQLAlchemy or a cache so interactive flows survive process restarts. The thin CRUD wrappers (`crud_order.py`, `crud_receipt.py`, etc.) are ready-made entrypoints for that storage.
- **Multiple products + pricing**  
  The `/order` endpoint currently hard-codes a product. Hook it into the product catalog and pass real `incomingAmount` values to `request_incoming_payment`.
- **Split payouts / fees**  
  `complete_payment` is the right place to inject business logic before the outgoing payment is constructed (e.g., split quotes or platform fees). The code already hints at this in the comments.
- **Webhook verification**  
  If you expose a webhook for the buyer wallet, reuse `paymentsparser.verify_response_hash` to confirm authenticity before continuing the grant.

With the above understanding, you can safely adapt the CRUD layer to new Open Payments use cases—every GNAP request and Open Payments resource creation lives inside `OpenPaymentsProcessor`, so extending the flow usually means wrapping or persisting its helper state rather than reimplementing the protocol.
