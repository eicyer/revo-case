FROM python:3.12-slim

WORKDIR /app

# Install Python deps first (separate layer — cached if requirements don't change)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY app ./app

# Document the port the container listens on (informational only)
EXPOSE 8000

# Default command when the container starts
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]