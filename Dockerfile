FROM python:3.13-slim

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Install dependencies only (no project source needed yet)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Now copy source and install the project itself
COPY mensa_mcp/ mensa_mcp/
RUN uv sync --frozen --no-dev

# Docker containers need to bind to 0.0.0.0 for external access
ENV MENSA_HOST=0.0.0.0
ENV MENSA_PORT=8080

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD sh -c 'curl -f "http://localhost:${MENSA_PORT:-8080}/health" || exit 1'

CMD ["uv", "run", "mensa-mcp"]
