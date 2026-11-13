FROM python:3.11-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir .

COPY content ./content
COPY data ./data
COPY templates ./templates
COPY static ./static

ENV HIGHGROUND_PROJECT_ROOT=/app
EXPOSE 8080
CMD ["uvicorn", "highground.web.main:app", "--host", "0.0.0.0", "--port", "8080"]
