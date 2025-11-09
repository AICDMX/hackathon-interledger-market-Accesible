# Native Language Market

Interledger-powered marketplace focused on accessible, native-language work. Funders post briefs, creators deliver multilingual media, and escrowed payouts flow through Interledger wallets.

## Repository Layout

| Path | Description |
| --- | --- |
| `marketplace-py/` | Django full-stack app (HTMX UI, DRF APIs, media uploads, custom user roles). See `marketplace-py/README.md` for framework-specific docs. |
| `services/payments/` | Node.js/TypeScript microservice that talks to Rafiki/Open Payments for wallet orchestration. Containerized via Dockerfile. |
| `wallet-nodejs/` | Lightweight Node.js script for manual wallet + incoming payment tests against Interledger testnet. |
| `docs/`, `startHere.md` | Product notes, feature checklists, and research artifacts. |
| `docker-compose.yml` | Defines the Django `web` app and the `payments` microservice. |

## Prerequisites

- Docker & Docker Compose v2+
- GNU Make (recommended for upcoming workflow automation)
- Optional local toolchains:
  - Python 3.11 + `uv` if you need to run Django without containers
  - Node 20.x + npm if you want to run the payments or wallet microservices directly

## Quick Start (Docker + Make)

We are standardizing on Make targets (to be added alongside the Docker workflows). When the Makefile lands you will be able to run:

```bash
make up        # builds and starts docker-compose stack
make down      # stops containers
make logs web  # streams logs from the Django service
```

Until the Makefile exists, run the equivalent Docker Compose commands manually:

```bash
docker compose up --build
docker compose down
docker compose logs -f web
```

The stack exposes:

- Django marketplace: http://localhost:8000 (serves UI + API, runs migrations & collectstatic on boot)
- Payments microservice: http://localhost:4001 (Express API that validates wallets and mediates payment grants)

## Service Details

- **Django (marketplace-py)**  
  - Ships jobs + submissions workflows, multilingual templates, and accessibility-focused UI.  
  - Uses SQLite for hackathon speed; media/static folders are volume-mounted for persistence.

- **Node payments microservice (`services/payments`)**  
  - Wraps the `@interledger/open-payments` SDK inside an Express server.  
  - **Validates wallet profiles** via `/api/wallet/profile` before initiating payments.
  - Manages three test wallet profiles:
    - `mvr5656` (Platform/Issuer) - Authenticates API calls
    - `edutest` (Funder/Sender) - Pays for jobs
    - `bobtest5656` (Creator/Receiver) - Receives payments
  - Private keys stored in `src/privates/` (mounted as Docker volume).
  - See `services/payments/README.md` for full API documentation.

- **Wallet CLI helper (`wallet-nodejs`)**  
  - Standalone script (`node index.js`) that requests grants and creates incoming payments against a configured wallet address.  
  - Requires `private.key`/`KEY_ID` pairs exported from Rafiki. Keep these secrets outside of version control.

## Developing Without Docker

- **Django**: `uv sync` then `uv run python manage.py runserver 0.0.0.0:8000`. See the app-level README for migrations, superuser creation, and localization tips.
- **Payments Service**: `npm install`, export your env vars, then `npm run dev`. Make sure port `4001` stays in sync with `docker-compose.yml`.
- **Wallet CLI**: `cd wallet-nodejs && npm install && node index.js` after setting your wallet parameters.

## Next Steps

1. Add the shared Makefile (`make up/down/logs/test`) so contributors have a single entry point.  
2. Document the payments service API surface (routes, payloads, event flow) under `docs/`.  
3. Wire Django job lifecycle events to the payments microservice once endpoints solidify.

For product context, roadmap, and localization targets, start with `startHere.md` and the artifacts in `docs/`.
