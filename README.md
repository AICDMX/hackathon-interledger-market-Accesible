# Native Language Market

Interledger-powered marketplace focused on accessible, native-language work. Funders post briefs, creators deliver multilingual media, and escrowed payouts flow through Interledger wallets. Designed for users that have limited to no written langauge ability. Most all things have custom implementation to do sound in native language.

Only Otomi Language voice added. We gathered during the hackathon through connections that work with indigenous populations.

We have two working branches. 
Main branch uses Contract style using python openpayments sdk
Node.js Microservice is on node-js-api. Uses escrow wallet solution.

## Repository Layout

| Path | Description |
| --- | --- |
| `marketplace-py/` | Django full-stack app (HTMX UI, DRF APIs, media uploads, custom user roles). See `marketplace-py/README.md` for framework-specific docs. |
| `docs/` | Product notes, feature checklists, and research artifacts. |
| `todo/` | Open and completed tasks. |
| `docker-compose.yml` | Defines the Django `web` service. |
| `media/` | User-uploaded media files (audio, images, etc.). |

## Prerequisites

- Docker & Docker Compose v2+
- GNU Make (for convenient workflow automation)
- Optional local toolchains:
  - Python 3.11 + `uv` if you need to run Django without containers

## Quick Start

### Using Make (Recommended)

```bash
make up          # Start all services
make logs        # View logs
make down        # Stop services
make help        # See all available commands
```

### Using Docker Compose

```bash
docker compose up --build
```

This will:
- Build and start the Django web service
- Run database migrations automatically
- Collect static files
- Load default jobs into the system
- Start the development server on http://localhost:8000

To stop:
```bash
docker compose down
# or
make down
```

To view logs:
```bash
docker compose logs -f web
# or
make logs-web
```

### Developing Without Docker

Using Make:
```bash
make dev-install      # Install dependencies
make dev-migrate      # Run migrations
make dev-collectstatic # Collect static files
make dev-run          # Start development server
```

Or manually:

1. **Install dependencies**:
   ```bash
   cd marketplace-py
   uv sync
   ```

2. **Run migrations**:
   ```bash
   uv run python manage.py migrate
   ```

3. **Load demo data** (optional):
   ```bash
   uv run python manage.py load_demo_users
   uv run python manage.py load_default_jobs
   # or with Make: make demo
   ```

4. **Collect static files**:
   ```bash
   uv run python manage.py collectstatic --noinput
   ```

5. **Start the development server**:
   ```bash
   uv run python manage.py runserver
   ```

6. **Access the application**:
   - Main site: http://127.0.0.1:8000/
   - Admin panel: http://127.0.0.1:8000/admin/
   - Translation admin: http://127.0.0.1:8000/rosetta/

## Demo Users

The system includes demo users for testing:

- **Funder**: `demo_funder` / `demo123` - Can create and manage jobs
- **Creators**: Multiple creator accounts (e.g., `maria_nahuatl`, `carlos_otomi`, `ana_quechua`) / `demo123` - Can submit work for jobs
- **Both roles**: `demo_both_1`, `demo_both_2` / `demo123` - Can both create jobs and submit work

Load demo users with:
```bash
uv run python manage.py load_demo_users
# or with Make: make load-users
# or load all demo data: make demo
```

## Service Details

- **Django (marketplace-py)**  
  - Full-stack Django application with HTMX for dynamic UI interactions
  - Jobs + submissions workflows with multilingual templates
  - Accessibility-focused UI with WCAG compliance
  - Uses SQLite for development; media/static folders are volume-mounted for persistence
  - Supports multiple languages: English, Spanish, Nahuatl, Otomi, Mazahua, Quechua, and more
  - Custom user model with roles: funder, creator, or both
  - Default jobs are automatically loaded on container startup

## Features

- **Multi-language Support**: Supports English, Spanish, Nahuatl, Otomi, Mazahua, Quechua, and other native languages
- **Accessibility**: WCAG-compliant templates with proper ARIA labels and semantic HTML
- **User Management**: Custom user model with roles (funder, creator, or both)
- **Job System**: 
  - Funders can create jobs with budgets
  - Creators can submit work for jobs
  - Funders can accept/reject submissions
- **Views**:
  - Job listings (browse available jobs)
  - My jobs (jobs posted by user)
  - Accepted jobs (jobs where user's submissions were accepted)

## Project Structure

```
marketplace-py/
??? jobs/              # Jobs app (job listings, submissions)
??? users/             # User app (authentication, profiles)
??? marketplace/       # Main project settings
??? templates/         # HTML templates
??? static/            # Static files (CSS, JS, images)
??? media/             # User-uploaded files
??? data/              # Demo data (users, jobs)
??? manage.py          # Django management script
```

## Documentation

- `docs/design.md` - Design system and tokens
- `docs/job-states.md` - Job state machine documentation
- `docs/open-payments.md` - Open Payments integration notes
- `docs/open-payments-sdk.md` - SDK usage documentation
- `marketplace-py/README.md` - Django-specific setup and usage

## Make Commands

The project includes a comprehensive Makefile for convenient workflow automation. Run `make help` to see all available commands.

### Docker Commands

Start and manage services with Docker Compose:

```bash
make up          # Start all services (builds images if needed)
make down        # Stop all services
make build       # Build Docker images without starting
make restart     # Stop and restart all services
make logs        # View logs from all services (follow mode)
make logs-web    # View logs from web service only (follow mode)
```

### Django Commands (in container)

Run Django management commands inside the running container:

```bash
make shell              # Open Django shell for interactive Python
make bash               # Open bash shell in container
make migrate            # Run database migrations
make makemigrations     # Create new migration files
make collectstatic      # Collect static files for production
make createsuperuser    # Create a Django superuser account
```

### Data Management

Load demo data for testing and development:

```bash
make demo        # Load both demo users and default jobs
make load-users  # Load demo users only (see Demo Users section)
make load-jobs   # Load default jobs only
```

### Local Development (without Docker)

Work on the project without Docker containers:

```bash
make dev-install      # Install Python dependencies with uv
make dev-migrate      # Run migrations locally
make dev-collectstatic # Collect static files locally
make dev-run          # Start Django dev server on localhost:8000
make dev-test         # Run Django test suite locally
make dev-shell        # Open Django shell locally
```

### Testing

Run tests inside the container:

```bash
make test            # Run Django test suite
make test-coverage   # Run tests with coverage report (requires pytest)
```

### Maintenance

Clean up generated files and containers:

```bash
make clean       # Remove containers, volumes, and generated files (__pycache__, .pyc, staticfiles)
make clean-db    # Remove SQLite database file (run 'make migrate' to recreate)
```

### Examples

**First-time setup:**
```bash
make up          # Start services
make demo        # Load demo data
# Access at http://localhost:8000
```

**Daily development:**
```bash
make up          # Start services
make logs-web    # Watch logs in another terminal
# Make changes, they'll auto-reload
```

**Local development without Docker:**
```bash
make dev-install      # Install dependencies
make dev-migrate      # Setup database
make dev-run          # Start server
```

**Reset everything:**
```bash
make clean       # Clean containers and files
make clean-db    # Remove database
make up          # Rebuild and start fresh
make demo        # Reload demo data
```

## Next Steps

1. Wire Django job lifecycle events to Interledger payment flows
2. Enhance UI/UX with additional accessibility features
3. Add comprehensive test coverage

For product context, roadmap, and localization targets, start with `startHere.md` and the artifacts in `docs/`.
