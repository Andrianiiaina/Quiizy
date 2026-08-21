# ===== Stage 1 : installation des dépendances =====
FROM python:3.12-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
# Stub minimal pour permettre à setuptools de résoudre le package app
RUN mkdir -p app && touch app/__init__.py

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --prefix=/install .

# ===== Stage 2 : image runtime minimale =====
FROM python:3.12-slim AS runtime

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system --gid 1001 appgroup \
    && useradd --system --uid 1001 --gid appgroup --no-create-home appuser

# Packages Python installés au stage builder
COPY --from=builder /install /usr/local

# Code source (écrase le stub du builder dans sys.path, cf. WORKDIR)
COPY --chown=appuser:appgroup . .

RUN chmod +x entrypoint.sh

USER appuser

EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
