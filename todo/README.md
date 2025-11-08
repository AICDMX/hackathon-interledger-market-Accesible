# Todo List Index

This directory contains organized todo lists for the Native Language Market project, split into logical sections.

## Todo Files

1. **[Priority Checklist](./priority_checklist.md)** - Must-ship features and critical first steps
2. **[User Pages](./user_pages.md)** - User authentication, profiles, wallet management
3. **[Transaction Pages](./transaction_pages.md)** - Escrow, payments, Interledger integration
4. **[Job Pages](./job_pages.md)** - Job posting, submissions, creator-led offers
5. **[Language & Accessibility](./language_accessibility.md)** - Multi-language support and accessibility features
6. **[Backend & Infrastructure](./backend_infrastructure.md)** - Models, APIs, file uploads, Interledger integration
7. **[Nice to Have](./nice_to_have.md)** - Optional features if time permits

## Quick Start

Start with the **[Priority Checklist](./priority_checklist.md)** to understand what must be shipped, then work through the sections based on priority and dependencies.

## Project Overview

Django marketplace for Native-language jobs where funders post work briefs and creators submit content. Focus on accessibility and multi-language support. Content types: text, video, audio, images.

**Note:** Escrow/payment features are planned for future iterations. Current focus is on a minimal accessible marketplace.

## Current Status

- ? Basic Django setup with models (User, Job, JobSubmission)
- ? Multi-language support configured
- ? Basic templates for jobs and users
- ? File upload handling - needs implementation
- ? Accessibility features - needs verification and enhancement
- ? Escrow system - moved to nice-to-have (future enhancement)
- ? Interledger integration - moved to nice-to-have (future enhancement)
- ? Creator-led offers - moved to nice-to-have (future enhancement)

## Focus: Minimal Accessible Marketplace

The current priority is building a **minimal accessible marketplace** that demonstrates:
- Job posting and submission workflow
- Multi-language support
- WCAG-compliant accessibility
- Basic user profiles

Payment/escrow features are planned for future iterations.
