FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.13.8 /uv /uvx /bin/

ENV UV_LINK_MODE=copy     PYTHONUNBUFFERED=1

WORKDIR /app/analytics

COPY analytics/pyproject.toml analytics/uv.lock ./
RUN uv sync --frozen --no-install-project

COPY analytics/dbt_project.yml analytics/profiles.yml ./
COPY analytics/macros ./macros
COPY analytics/models ./models
COPY analytics/tests ./tests

ENV PATH="/app/analytics/.venv/bin:$PATH"
RUN python -c "import duckdb; duckdb.sql('install httpfs')"

CMD ["dbt", "build", "--target", "cloud", "--profiles-dir", "."]
