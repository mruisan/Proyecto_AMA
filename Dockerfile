# Usamos una imagen oficial de Python ligera
FROM python:3.11-slim

# Establecemos el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copiamos el archivo de requisitos para instalar las dependencias
COPY requirements.txt .

# Instalamos las dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos todo el resto del código fuente del proyecto al contenedor
COPY . .

# Exponemos el puerto 5000 que es donde corre Flask
EXPOSE 5000

# Comando para arrancar la aplicación en producción (Gunicorn es más seguro que app.run)
# Instalamos gunicorn dinámicamente si no está en tu requirements
RUN pip install gunicorn

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:create_app()"]