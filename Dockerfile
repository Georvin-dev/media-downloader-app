FROM python:3.10-slim

# Instalar ffmpeg
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Comando exacto para arrancar Flask en Render con gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:10000", "downloaderapp:app"]
