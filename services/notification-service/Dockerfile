# Multi-stage build for Python microservice
FROM python:3.13-slim AS builder

WORKDIR /build

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --user -r requirements.txt

# ============================================
# Final stage
FROM python:3.13-slim

WORKDIR /app

# Create non-root user
RUN useradd -m -u 1001 -s /bin/bash serviceuser

# Copy installed packages from builder
COPY --from=builder /root/.local /home/serviceuser/.local

# Copy application code
COPY --chown=serviceuser:serviceuser app/ /app/app/

# Set Python path
ENV PATH=/home/serviceuser/.local/bin:$PATH
ENV PYTHONPATH=/app

# Switch to non-root user
USER serviceuser

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
  CMD python -c "import sys; sys.exit(0)"

# Run service
CMD ["python", "-m", "app.main"]
