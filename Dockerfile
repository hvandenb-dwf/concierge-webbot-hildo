# Gebruik een slanke Python-image
FROM python:3.11-slim

# Zet werkdirectory
WORKDIR /app

# Kopieer requirements (voor niet-elevenlabs packages)
COPY requirements.txt .

# Systeemafhankelijkheden en pip-installatie
RUN apt-get update && \
    apt-get install -y gcc libffi-dev libssl-dev curl git && \
    pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip uninstall -y elevenlabs || true && \
    pip install --no-cache-dir git+https://github.com/elevenlabs/elevenlabs-python.git@v1.0.4

# Kopieer de volledige app
COPY . .

# Start de applicatie op Render
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "10000"]
