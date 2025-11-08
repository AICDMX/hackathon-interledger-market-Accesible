# Backend & Infrastructure

## Models & Database
- [ ] Verify all models are complete:
  - User model (wallet endpoint, languages) ?
  - Job model (status, deliverable types) ?
  - JobSubmission model (file uploads) ?
- [ ] Create EscrowTransaction model:
  - Job reference
  - Amount
  - Status (pending, funded, released, refunded)
  - Timestamps
  - ILP transaction ID
- [ ] Create CreatorAsset model (for ready-made assets):
  - Creator reference
  - Title, description
  - Content type
  - Language
  - Price
  - File uploads
  - Status (available, sold)
- [ ] Database migrations
- [ ] Seed demo data

## File Upload System
- [ ] File upload handling for:
  - Text files
  - Video files
  - Audio files
  - Image files
- [ ] File storage configuration (local or S3)
- [ ] File size limits
- [ ] File type validation
- [ ] File preview functionality
- [ ] Auto transcription for audio/video (nice to have)
- [ ] Thumbnail generation for images/videos (nice to have)

## API & Views
- [ ] DRF API setup (if using REST API)
- [ ] Job CRUD endpoints
- [ ] Submission upload pipeline
- [ ] File serving endpoints
- [ ] Escrow API endpoints
- [ ] Payment API endpoints
- [ ] User API endpoints

## Interledger Integration (Nice to Have - Future)
- [ ] Interledger test connector setup
- [ ] Escrow stubs implementation
- [ ] Payment initiation
- [ ] Payment release on acceptance
- [ ] Payment refund on rejection
- [ ] ILP transaction tracking
- [ ] Error handling for ILP failures

## Security & Validation
- [ ] CSRF protection (verify)
- [ ] File upload security
- [ ] User permission checks
- [ ] Budget validation (numeric, positive)
- [ ] Language code validation
- [ ] File type and size validation

## Development & Deployment Infrastructure
- [ ] Create Makefile with the following targets:
  - **Development Setup:**
    - `make setup` - Initial project setup (install dependencies for all services)
    - `make setup-django` - Setup Django marketplace-py (install uv dependencies, run migrations, create superuser)
    - `make setup-payments` - Setup payments service (npm install)
    - `make setup-wallet` - Setup wallet-nodejs service (npm install)
    - `make setup-all` - Setup all services
  - **Development Commands:**
    - `make dev` - Run all services locally (without Docker)
    - `make dev-django` - Run Django dev server
    - `make dev-payments` - Run payments service in dev mode
    - `make dev-wallet` - Run wallet service in dev mode
    - `make migrate` - Run Django migrations
    - `make makemigrations` - Create Django migrations
    - `make collectstatic` - Collect Django static files
    - `make createsuperuser` - Create Django superuser
  - **Docker Commands:**
    - `make docker-build` - Build all Docker images
    - `make docker-up` - Start all services with docker-compose
    - `make docker-down` - Stop all Docker services
    - `make docker-logs` - View Docker logs
    - `make docker-restart` - Restart Docker services
    - `make docker-clean` - Stop and remove containers, volumes, and images
  - **Database Commands:**
    - `make db-reset` - Reset Django database (drop and recreate)
    - `make db-migrate` - Run Django migrations
    - `make db-shell` - Open Django database shell
  - **Testing & Quality:**
    - `make test` - Run all tests
    - `make test-django` - Run Django tests
    - `make lint` - Run linters
    - `make format` - Format code
  - **Utilities:**
    - `make clean` - Clean temporary files and caches
    - `make help` - Show available Makefile targets
