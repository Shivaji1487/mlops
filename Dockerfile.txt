FROM python:3.11-slim

WORKDIR /app

# Install minimal requirements
RUN pip install --no-cache-dir pandas

COPY app.py .

CMD ["python", "app.py"]