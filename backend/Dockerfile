FROM python:3.12-slim

WORKDIR /app

# System deps for psycopg (binary wheel avoids needing build tools, but
# libpq is still required at runtime on slim images).
RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq5 \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
COPY app ./app

RUN pip install --no-cache-dir .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
