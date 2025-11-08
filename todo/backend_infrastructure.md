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
