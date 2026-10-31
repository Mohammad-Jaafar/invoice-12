FROM python:3.14-slim-trixie
 
COPY --from=ghcr.io/astral-sh/uv:0.13.5 /uv /uvx /bin/
 
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_NO_DEV=1 \
    UV_PYTHON_DOWNLOADS=never \
    PYTHONUNBUFFERED=1
 
WORKDIR /app
 
COPY pyproject.toml uv.lock .python-version ./
RUN uv sync --locked --no-install-project
 
COPY . .
RUN uv sync --locked
 
RUN useradd --create-home --uid 1000 appuser
USER appuser
 
ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
