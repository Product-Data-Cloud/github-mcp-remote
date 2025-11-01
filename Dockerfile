FROM python:3.12-slim

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml .
COPY requirements.txt .
COPY server.py .

RUN uv pip install --system -r requirements.txt

EXPOSE 8080

ENV PORT=8080

CMD ["fastmcp", "run", "server.py", "--host", "0.0.0.0", "--port", "8080"]
