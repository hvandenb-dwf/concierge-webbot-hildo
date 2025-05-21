# Gebruik officiële Python base image
FROM python:3.11-slim

# Zet werkdirectory
WORKDIR /app

# Kopieer requirements
COPY requirements.txt .

# Installeer systeemafhankelijkheden en Python packages
RUN apt-get update && \
    apt-get install -y gcc libffi-dev libssl-dev curl git && \
    pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Kopieer alle app-bestanden
COPY . .

# Start commando
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "10000"]
