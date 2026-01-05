# Use the official Playwright Python image which includes all necessary browser dependencies
FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

# Set work directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Ensure playwright browsers are installed (though they should be in the base image)
RUN playwright install chromium

# Default command (can be overridden in docker.yaml)
ENTRYPOINT ["python", "abn_pdf_scraper.py"]
CMD ["--help"]
