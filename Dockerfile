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

# Create directories for media and static files (checkpoint 3: static directories)
RUN mkdir -p /app/src/media /app/src/staticfiles /app/src/locale

# Copy project code last (checkpoint 4: only this layer rebuilds when src changes)
COPY src/ ./src/

# Expose port
EXPOSE 8000

# Run migrations and start server
CMD ["sh", "-c", "cd src && python manage.py migrate --noinput && python manage.py collectstatic --noinput && python manage.py runserver 0.0.0.0:8000"]
