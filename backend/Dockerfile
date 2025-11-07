# Use Python slim image for smaller size
FROM python:3.13-slim AS builder

# Install uv for faster dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set working directory
WORKDIR /app

# Copy dependency files
COPY requirements.txt .
COPY pyproject.toml .

# Create virtual environment and install dependencies with uv (using native TLS)
RUN uv venv /opt/venv && \
    . /opt/venv/bin/activate && \
    uv pip install --native-tls --no-cache -r requirements.txt

# Production stage
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Copy application code
COPY app /app/app
COPY routers /app/routers
COPY config /app/config
COPY main.py /app/

# Expose port
EXPOSE 8001

# Set Python to run in unbuffered mode
ENV PYTHONUNBUFFERED=1
ENV PATH="/opt/venv/bin:$PATH"

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8001/health')" || exit 1

# Run the application with granian
CMD ["granian", "--interface", "asgi", "main:app", "--host", "0.0.0.0", "--port", "8001"]

