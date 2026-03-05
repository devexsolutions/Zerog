
# Usa una imagen oficial de Python
FROM python:3.10-slim

# Instala dependencias del sistema para Tesseract y Poppler (para PDFs)
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-spa \
    libtesseract-dev \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Establece el directorio de trabajo
WORKDIR /app

# Copia los requirements e instálalos
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia el código del backend a /app/backend para mantener la estructura de paquete
COPY . /app/backend

# Establece la variable de entorno PYTHONPATH
ENV PYTHONPATH=/app:/app/backend

# Crea el directorio de uploads si no existe
RUN mkdir -p /app/backend/uploads && mkdir -p /app/backend/db

# Expone el puerto 8000
EXPOSE 8000

# Comando para correr la aplicación usando el módulo backend
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
