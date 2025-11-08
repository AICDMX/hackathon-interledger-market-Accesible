# Django Marketplace Setup

This is a Django-based marketplace system with accessibility and multi-language support for an Interledger-powered exchange.

**Note**: All project code is located in the `src/` directory.

## Features

- **Multi-language Support**: Supports English, Spanish, Nahuatl, Otomi, Mazahua, and Quechua
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

## Setup Instructions

1. **Install uv** (if not already installed):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Install dependencies**:
   ```bash
   uv sync
   ```

3. **Run migrations**:
   ```bash
   cd marketplace-py
   uv run python manage.py makemigrations
   uv run python manage.py migrate
   ```

4. **Create a superuser** (optional, for admin access):
   ```bash
   uv run python manage.py createsuperuser
   ```

5. **Collect static files**:
   ```bash
   uv run python manage.py collectstatic --noinput
   ```

6. **Run the development server**:
   ```bash
   uv run python manage.py runserver
   ```

7. **Access the application**:
   - Main site: http://127.0.0.1:8000/
   - Admin panel: http://127.0.0.1:8000/admin/
   - Translation admin: http://127.0.0.1:8000/rosetta/

## Project Structure

```
.
??? src/                    # All project code is located here
?   ??? marketplace/        # Main project settings
?   ??? users/              # User app (authentication, profiles)
?   ??? jobs/               # Jobs app (job listings, submissions)
?   ??? templates/          # HTML templates
?   ??? static/             # Static files (CSS, JS, images)
?   ??? media/              # User-uploaded files
?   ??? manage.py           # Django management script
??? pyproject.toml          # Project dependencies (uv)
??? requirements.txt        # Legacy requirements file
```

## Usage

1. **Register/Login**: Create an account or login
2. **Create a Job**: As a funder, post a job with description, language, and budget
3. **Browse Jobs**: View available jobs and filter by language
4. **Submit Work**: As a creator, submit work for open jobs
5. **Accept Submissions**: As a funder, review and accept submissions
6. **View Accepted Jobs**: See jobs where your submissions were accepted

## Language Support

The system supports multiple languages:
- English (en)
- Spanish (es)
- Nahuatl (nah)
- Otomi (oto)
- Mazahua (maz)
- Quechua (que)

Users can switch languages using the language selector in the header.

## Accessibility Features

- Semantic HTML5 elements
- ARIA labels and roles
- Keyboard navigation support
- High contrast colors
- Skip to main content link
- Focus indicators
- Screen reader friendly

## Next Steps

- Integrate Interledger escrow system
- Add file upload handling for submissions
- Implement payment processing
- Add email notifications
- Enhance UI/UX
