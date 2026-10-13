FROM python:3.11-slim

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install system binaries via apt-get
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browser and Linux system dependencies
RUN playwright install chromium --with-deps

# Copy project source files and assets
COPY . .

# Ensure runtime directories exist
RUN mkdir -p data/input data/output data/temp

# Expose Streamlit port
EXPOSE 8501

# Launch Streamlit in headless mode
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]
