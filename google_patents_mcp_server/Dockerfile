FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080 \
    HOST=0.0.0.0 \
    MCP_TRANSPORT=streamable-http

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all application files directly into /app
COPY . .

EXPOSE 8080

CMD ["python", "main.py", "--transport", "streamable-http"]

