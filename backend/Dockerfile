FROM python:3.12-slim

WORKDIR /app

# libpq is required at runtime by psycopg on slim images.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq5 \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
COPY app ./app
RUN pip install --no-cache-dir .

# Migrations and the seed script must exist inside the image so that
# `docker compose exec backend alembic upgrade head` and
# `docker compose exec backend python -m scripts.seed_demo_data` work.
COPY alembic.ini ./
COPY migrations ./migrations
COPY scripts ./scripts

# Run as an unprivileged user.
RUN useradd --create-home --uid 10001 appuser
USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
