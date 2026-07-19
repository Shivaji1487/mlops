FROM python:3.11-slim

WORKDIR /app

# 🌟 बदलाव यहाँ है: pandas के साथ mlflow भी जोड़ दिया है
RUN pip install --no-cache-dir pandas mlflow

COPY app.py .

CMD ["python", "app.py"]