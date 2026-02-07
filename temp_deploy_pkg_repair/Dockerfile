# Base Image for Frontend Build
FROM node:20 AS frontend-builder

# Set working directory for frontend
WORKDIR /app/web

# Copy package management files
COPY web/package.json ./
# Assuming yarn.lock exists, otherwise comment out
COPY web/yarn.lock ./

# Copy the rest of the frontend source code
COPY web/ .

# Copy project config for Nx (it looks for it in root)
COPY pyproject.toml /app/pyproject.toml

# Install dependencies
# Using --frozen-lockfile for reproducible builds
RUN yarn install --network-timeout 100000

# Build the specific app (Synapse)
# Output will be in dist/apps/synapse (lowercase s)
RUN yarn synapse:build


# Base Image for Backend and Runtime
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies required for building Python packages and runtime (e.g., PostgreSQL client)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
ENV POETRY_VERSION=2.1.0
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="/root/.local/bin:$PATH"

# Copy project configuration files
COPY pyproject.toml poetry.lock README.md ./

# Copy local SDK dependency
# Copy local SDK dependency
COPY synapse-sdk/ ./synapse-sdk/

# Copy Backend Source Code (Required for pip install -e .)
COPY synapse/ ./synapse/

# Install Python dependencies globally
# we use poetry export to ensure we get a requirements.txt that pip can handle reliably
# checking for poetry-plugin-export support
RUN poetry self add poetry-plugin-export \
    && sed -i 's|file:./synapse-sdk|file:///app/synapse-sdk|' pyproject.toml \
    && poetry lock \
    && poetry export --format requirements.txt --output requirements.txt --without-hashes \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install gunicorn \
    && pip install --no-deps -e . \
    && pip list
# Copy root level scripts if needed, though they seem to be in synapse/

# We will verify location content copy.

# Copy Frontend Build Artifacts to where Django expects them
# Settings expect: ../../web/dist/apps/Synapse (relative to synapse/core)
# So we need to reconstruct /app/web/dist/apps/Synapse
COPY --from=frontend-builder /app/web/dist/apps/synapse /app/synapse/core/static/react-app/
# Note: dist/libs is not produced by the build, so we skip it

# Environment Variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV DJANGO_SETTINGS_MODULE=synapse.core.settings.synapse
ENV PORT=8080
ENV PYTHONPATH=/app:/app/synapse

# Create a non-root user for security (Optional but recommended, skipping for simplicity in this guide)

# Collect Static Files
# We set a dummy SECRET_KEY purely for this step as it's required by Django
RUN SECRET_KEY=dummy_build_key python synapse/manage.py collectstatic --noinput

# Expose the port
EXPOSE 8080

# Start the application using Gunicorn
# Adjust workers/threads based on instance resources
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "--timeout", "120", "synapse.core.wsgi:application"]
