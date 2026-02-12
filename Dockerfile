FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY server.py .

# Railway injects PORT automatically
ENV PORT=8080

EXPOSE ${PORT}

CMD ["python", "server.py"]
