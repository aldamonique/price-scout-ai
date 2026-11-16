FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.13.8 /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1     UV_LINK_MODE=copy     PYTHONUNBUFFERED=1

WORKDIR /app/api

COPY api/pyproject.toml api/uv.lock api/README.md ./
RUN uv sync --frozen --no-dev --no-install-project

COPY api/src ./src
COPY api/scripts ./scripts
COPY api/evals ./evals
COPY analytics/macros /app/analytics/macros
COPY analytics/models/gold /app/analytics/models/gold
RUN uv sync --frozen --no-dev

ENV PATH="/app/api/.venv/bin:$PATH"
RUN python -c "import duckdb; duckdb.sql('install httpfs')"

EXPOSE 8000
CMD ["uvicorn", "price_scout.main:app", "--host", "0.0.0.0", "--port", "8000"]
