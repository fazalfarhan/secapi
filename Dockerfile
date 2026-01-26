FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    && rm -rf /var/lib/apt/lists/* \
    && wget -qO /tmp/trivy.rpm https://github.com/aquasecurity/trivy/releases/download/v0.55.0/trivy_0.55.0_Linux-ARM64.deb \
    && dpkg -i /tmp/trivy.rpm \
    && rm /tmp/trivy.rpm

# Install Python dependencies
COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create logs directory
RUN mkdir -p logs

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
