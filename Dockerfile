FROM python:3.11-slim

# On force Python à ne pas mettre en cache le bytecode (.pyc) et à afficher immédiatement les logs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Création d'un utilisateur non-root pour des raisons de sécurité
RUN useradd -m appuser

# Installation des dépendances
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copie du code de l'application
COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini .

# On donne la propriété du dossier /app à appuser
RUN chown -R appuser:appuser /app

# On bascule sur l'utilisateur non-root
USER appuser

# Exposition du port
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]