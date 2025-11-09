# Open Payments SDK layout

`backend/app/app/open_payments_sdk` is a small, framework-free client that knows how to talk to Open Payments wallets, authorization servers, and resource servers. The CRUD layer (`OpenPaymentsProcessor`) imports it, but the pieces are reusable elsewhere in the backend.

## High-level architecture

- **Configuration (`configuration.py`)**  
  Provides a default user-agent and logging formatter. `OpenPaymentsClient` uses it to attach a stream handler so SDK logging is consistent with the rest of the app.
- **HTTP transport (`http.py`)**  
  Thin wrapper around `httpx`. `HttpClient` builds requests, injects JSON/payload data, and enforces a global timeout when sending. All API modules receive a shared instance so connection behavior is consistent.
- **Security helpers (`gnap_utils/…`)**  
  `SecurityBase` handles GNAP requirements: computing `Content-Digest` headers, signing requests with Ed25519 (via http-message-signatures), and creating authorization headers (`GNAP <access_token>`). Subclasses like `Grants`, `IncomingPayments`, and `Quotes` inherit this to avoid duplicating crypto details.
- **Models (`models/…`)**  
  Pydantic schemas for grants, access tokens, wallet addresses, quotes, and payments. These mirror the Open Payments specification and power both request serialization and response validation.
- **Utility functions (`utils/utils.py`)**  
  Shared constants such as JSON content-type headers and the covered component list used when signing HTTP messages.

## Client surface

`client/client.py` exposes `OpenPaymentsClient`, the object the rest of the backend instantiates. Construction requires:

```python
OpenPaymentsClient(
    keyid=settings.TEST_SELLER_KEY_ID,
    private_key=settings.TEST_SELLER_KEY,
    client_wallet_address=settings.TEST_SELLER_WALLET,
    http_client=HttpClient(http_timeout=10.0),
)
```

Internally the client wires together:

- `Wallet`: read-only helper for fetching wallet addresses (`GET https://wallet/.well-known/open-payments`) and their JWKS sets;
- `Grants` and `AccessTokens`: POST/DELETE helpers for GNAP grant requests, continuations, and access-token rotation;
- `IncomingPayments`, `OutgoingPayments`, `Quotes`: resource-server helpers for CRUD on Open Payments primitives.

Because each sub-client is preconfigured with the same key material and HTTP client, callers only need to pass the target endpoint URL and the relevant Pydantic schema instance. The SDK takes care of marshalling payloads, attaching access tokens, signing, and validating responses.

## Request lifecycle

Every network call follows the same steps:

1. Accept a Pydantic schema (e.g., `GrantRequest`, `IncomingPaymentRequest`) and call `model_dump()` to obtain a JSON payload.
2. Build the request with `HttpClient.build_request`, injecting JSON/body/params as needed.
3. If there is a body, call `SecurityBase.set_content_digest` so the `Content-Digest` header matches the payload hash.
4. Sign the request with `SecurityBase.sign_request`, covering `@method`, `@target-uri`, `content-type`, `content-digest`, `content-length`, and optionally `authorization`.
5. Send the request via `HttpClient.send`. The helper raises on non-2xx responses, so callers can rely on exceptions for failures.
6. Deserialize the response JSON back into the correct schema (`Grant`, `Quote`, `OutgoingPayment`, etc.) before returning it to the caller.

This keeps GNAP signing and validation centralized, making it easy to extend the SDK with new resource types without copying boilerplate.

## Extending the SDK

- **Add new resources**  
  Create a Pydantic schema under `models`, write a small API wrapper under `api/` that inherits `SecurityBase`, and expose it from `OpenPaymentsClient`.
- **Custom timeouts or logging**  
  Pass a configured `HttpClient` or `Configuration` instance when instantiating `OpenPaymentsClient` to override the defaults (e.g., longer timeouts in development).
- **Alternate transports**  
  Since `HttpClient` only exposes `build_request` and `send`, you can subclass it to add retries, telemetry, or async support without touching the higher-level API code.

## Relationship to CRUD layer

`OpenPaymentsProcessor` is a consumer of this SDK: it composes the sub-clients to implement the nine-step Open Payments purchase flow. If you need to perform lower-level operations (e.g., rotate access tokens, list historical outgoing payments, fetch JWKS for wallet verification), import the relevant `OpenPaymentsClient` property directly instead of duplicating HTTP logic.
