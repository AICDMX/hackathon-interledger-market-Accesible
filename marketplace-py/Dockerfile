FROM python:3.11-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set working directory
WORKDIR /app

# Set environment variables (rarely change, so cache early)
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=marketplace.settings
ENV PATH="/app/.venv/bin:$PATH"

# Copy dependency files first (checkpoint 1: only rebuilds if dependencies change)
COPY pyproject.toml uv.lock ./

# Install dependencies (checkpoint 2: expensive step, cached unless pyproject.toml/uv.lock change)
RUN uv sync --frozen --no-install-project

# Create directories for static files (checkpoint 3: static directories)
# Note: media directory will be created by COPY command
RUN mkdir -p /app/staticfiles /app/locale

# Copy project code last (checkpoint 4: only this layer rebuilds when marketplace-py changes)
# Since Dockerfile is now in marketplace-py/, copy all contents from build context
COPY . ./

# Explicitly copy media files to ensure they're included
COPY media/ /app/media/

# Expose port
EXPOSE 8000

# Run migrations/collectstatic, then launch production-ready gunicorn
CMD ["sh", "-c", "python manage.py migrate --noinput && python manage.py collectstatic --noinput && gunicorn marketplace.wsgi:application --bind 0.0.0.0:8000"]
