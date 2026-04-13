FROM python:3.12-slim

WORKDIR /app

# Instala Poetry
RUN pip install poetry

# Copia los archivos del proyecto
COPY . /app

# Instala las dependencias desde requirements.txt usando Poetry
# Si usas un pyproject.toml real, puedes usar:
COPY pyproject.toml poetry.lock* /app/
RUN poetry install --no-root

# Comando de ejecución principal vía poetry
CMD ["poetry", "run", "python", "main.py"]
