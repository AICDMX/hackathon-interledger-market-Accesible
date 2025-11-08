FROM python:3.11-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml ./

# Install dependencies
RUN uv sync --frozen --no-install-project

# Copy project code
COPY src/ ./src/

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=marketplace.settings
ENV PATH="/app/.venv/bin:$PATH"

# Create directories for media and static files
RUN mkdir -p /app/src/media /app/src/staticfiles /app/src/locale

# Expose port
EXPOSE 8000

# Run migrations and start server
CMD ["sh", "-c", "cd src && python manage.py migrate --noinput && python manage.py collectstatic --noinput && python manage.py runserver 0.0.0.0:8000"]
