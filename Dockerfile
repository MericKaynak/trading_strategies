FROM python:3.11-slim-bookworm

# uv Umgebungsvariablen
ENV UV_PROJECT_ENVIRONMENT="/app/.venv"
ENV PATH="/app/.venv/bin:$PATH"
ENV UV_COMPILE_BYTECODE=1
# Verhindert, dass uv versucht, eine neue Python-Version zu installieren (wir nutzen das Image)
ENV UV_PYTHON_DOWNLOADS=never

WORKDIR /app

# Installiere uv (wir kopieren einfach das Binary aus dem offiziellen Image)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Zeitzone setzen (slim-Image benötigt apt-get update)
RUN apt-get update && apt-get install -y --no-install-recommends tzdata && \
    ln -fs /usr/share/zoneinfo/Europe/Berlin /etc/localtime && \
    dpkg-reconfigure --frontend noninteractive tzdata && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Zuerst nur die Dependency-Dateien kopieren für optimales Layer-Caching
COPY pyproject.toml uv.lock ./

# Abhängigkeiten installieren (ohne das Projekt selbst zu installieren)
# --frozen stellt sicher, dass die uv.lock exakt eingehalten wird
RUN uv sync --frozen --no-install-project --no-dev

# Den restlichen Code kopieren
COPY . .

# Jetzt das Projekt selbst installieren (registriert die src-Ordner etc.)
RUN uv sync --frozen --no-dev

# WICHTIG: PYTHONPATH setzen, damit Python die Module im 'src' Ordner findet
ENV PYTHONPATH=/app/src

# App starten. Da wir den Pfad in den ENV gesetzt haben, 
# führen wir die Datei im src-Ordner direkt aus.
CMD ["uv", "run", "-m", "src/main.py"]