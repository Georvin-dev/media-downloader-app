FROM python:3.10-slim

WORKDIR /app

# Copiar e instalar dependencias primero
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todo el código del proyecto
COPY . .

# Exponer el puerto predeterminado de Render
EXPOSE 10000

# Arrancar la app con gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:10000", "downloaderapp:app"]
