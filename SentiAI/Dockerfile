# Use Python 3.11 slim image
FROM python:3.11-slim

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Install system dependencies required by OpenCV and PyTorch/YOLOv8
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libglib2.0-0 \
    libgomp1 \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory inside the container
WORKDIR /sentinel-ai

# Copy requirements file first to cache docker layer
COPY requirements.txt .

# Install Python requirements
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Create volume mounts for databases, videos, and logs
RUN mkdir -p videos logs data

# Expose FastAPI port
EXPOSE 8000

# Set environment variables for runtime
ENV VIDEO_SOURCE=mock
ENV CONFIDENCE_THRESHOLD=0.45
ENV DATABASE_URL=sqlite:///data/sentinel.db
ENV LOG_LEVEL=INFO

# Run FastAPI backend via Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
