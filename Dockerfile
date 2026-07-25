FROM python:3.11-slim

WORKDIR /app

# Environment variables to prevent buffer lag in logs
ENV PYTHONUNBUFFERED=1

# Copy & install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy ONLY the serving script into the runtime container
COPY serve.py .

EXPOSE 8000

# Container runs the continuous FastAPI inference server
CMD ["python", "serve.py"]