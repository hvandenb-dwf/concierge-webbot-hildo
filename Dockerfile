FROM python:3.11-slim

# Zet werkdirectory binnen container
WORKDIR /app

# Kopieer requirements.txt en installeer afhankelijkheden
COPY requirements.txt .

RUN apt-get update && \
    apt-get install -y gcc libffi-dev libssl-dev curl git && \
    pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip uninstall -y elevenlabs || true && \
    pip install --no-cache-dir git+https://github.com/elevenlabs/elevenlabs-python.git@v1.0.4 && \
`   python -c "import elevenlabs; print('✅ ElevenLabs versie:', getattr(elevenlabs, '__version__', 'onbekend'))"


# Kopieer de volledige projectmap
COPY . .

# Start FastAPI via Uvicorn op poort 10000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "10000"]
