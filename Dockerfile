FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install ".[api,openai,redis,mcp]"

EXPOSE 8000
ENV LLM_PROVIDER=stub MEMORY_BACKEND=memory APPROVAL_MODE=manual

CMD ["uvicorn", "taskpilot.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
