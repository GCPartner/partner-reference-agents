FROM python:3.11-slim

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy agent source
COPY . .

# Cloud Run uses PORT env var
ENV PORT=8080
ENV GOOGLE_GENAI_USE_VERTEXAI=1

EXPOSE 8080

CMD ["python", "server.py"]
