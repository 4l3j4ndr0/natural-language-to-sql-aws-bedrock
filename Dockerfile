FROM python:3.13-slim

WORKDIR /app

# Copy requirements first for better layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PORT=5000 \
    DEBUG=False \
    LOG_LEVEL=INFO

# Create non-root user for security
RUN adduser --disabled-password --gecos "" appuser
RUN chown -R appuser:appuser /app
USER appuser

# Run the application with gunicorn
CMD gunicorn --bind 0.0.0.0:$PORT app:app