# Gebruik officiële Python-image als basis
FROM python:3.11-slim

# Werkdirectory binnen de container
WORKDIR /app

# Kopieer dependency-bestand
COPY requirements.txt .

# Installeer systeempakketten en Python dependencies
RUN apt-get update && \
    apt-get install -y gcc libffi-dev libssl-dev curl git && \
    pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip uninstall -y elevenlabs || true && \
    pip install git+https://github.com/elevenlabs/elevenlabs-python.git@v1.0.4 && \
    python -c "import elevenlabs; print('✅ ElevenLabs versie:', getattr(elevenlabs, '__version__', 'onbekend'))"

# Kopieer alle app-bestanden
COPY . .

# Start de FastAPI-app met Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "10000"]
