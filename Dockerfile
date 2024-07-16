# Usa una imagen base oficial de Python
FROM python:3.9-slim

# Establece la variable de entorno para habilitar la salida no almacenada en búfer
ENV PYTHONUNBUFFERED=1

# Instala dependencias necesarias, incluyendo rclone
RUN apt-get update && apt-get install -y \
    curl \
    && curl https://rclone.org/install.sh | bash \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Establece el directorio de trabajo en el contenedor
WORKDIR /app

# Copia los archivos necesarios al contenedor
COPY distribute.py /app/distribute.py
COPY rclone.conf /app/rclone.conf
COPY requirements.txt /app/requirements.txt

# Instala las dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Define el punto de entrada que ejecutará el script
ENTRYPOINT ["python", "distribute.py"]