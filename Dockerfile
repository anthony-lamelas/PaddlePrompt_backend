# Use Python 3.9 as specified in Pipfile
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies for PDF processing and other libraries
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    poppler-utils \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code and WSGI files
COPY src/ ./src/
COPY api.py ./
COPY wsgi.py ./
COPY gunicorn.conf.py ./

# Create a non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 10000

# Set environment variables
ENV PYTHONPATH=/app
ENV FLASK_APP=api.py
ENV FLASK_ENV=production

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:10000/health || exit 1

# Run the application with Gunicorn
CMD ["gunicorn", "--config", "gunicorn.conf.py", "wsgi:app"] 