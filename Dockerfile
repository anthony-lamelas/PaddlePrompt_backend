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
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy .env file for environment variables
COPY .env .

# Copy source code
COPY src/ ./src/

# Create a non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 5000

# Set environment variables
ENV PYTHONPATH=/app
ENV FLASK_APP=src/api.py

# Run the application
CMD ["python", "src/api.py"] 