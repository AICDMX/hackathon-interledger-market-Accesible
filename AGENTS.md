# Repository Guidelines

## Project Structure & Module Organization
- `marketplace-py/` hosts the Django app (apps live under `jobs/`, `users/`, `marketplace/`, with templates and static assets alongside). Use `templates/components/` for shared partials and keep CSS in Tailwind utilities powered by the tokens defined in `docs/design.md`.
- `services/payments/` contains the Node-based Interledger microservice wired up in `docker-compose.yml`.
- `wallet-nodejs/` offers Open Payments client experiments; keep demo scripts here to avoid polluting the Django runtime.
- `docs/` and `todo/` track design direction, tokens, and workstreams; update them whenever UX or architecture shifts.

## Build, Test, and Development Commands
- Install Python deps via `cd marketplace-py && uv sync`.
- Apply migrations and collect static assets with `uv run python manage.py migrate` and `uv run python manage.py collectstatic --noinput`.
- Launch the dev server through `uv run python manage.py runserver` or bring everything up with `docker compose up web payments` from the repo root.
- Node artifacts: run `npm install` inside `services/payments/` or `wallet-nodejs/`, then `npm start`/`node index.js` for manual tests.

## Coding Style & Naming Conventions
- Follow PEP 8 (4-space indents, snake_case for Python, PascalCase for Django models/forms). Template blocks use kabab-case IDs and Tailwind utility classes referencing shared tokens—avoid inline styles entirely.
- JavaScript/TypeScript in services follows ESLint’s recommended style with camelCase variables.
- Name files by domain (`jobs/views_offer.py`, `services/payments/routes/quote.js`) so features stay discoverable.

## Testing Guidelines
- Keep unit tests beside each app (`jobs/tests/`, `users/tests/`). Run them through `uv run python manage.py test`.
- For services, add Jest or tap-based tests under `services/payments/__tests__/` and run `npm test`.
- Add fixtures for multilingual data, and cover both wallet roles (funder/creator) plus escrow paths.
- Aim for meaningful coverage on flows touching Interledger endpoints; attach sample responses under `services/payments/fixtures/`.

## Commit & Pull Request Guidelines
- Write imperative, component-scoped commits similar to `jobs: add escrow release hook`. Keep summaries under 72 chars and explain context in the body when needed.
- Each PR must include: purpose summary, list of commands/tests run, screenshots or curl output for UX/API changes, and links to related issues or TODO items.
- Request review from the domain owner (design system, payments, or wallet) before merging, and wait for CI (tests + lint) to pass.***
