FROM python:3.12-slim

WORKDIR /app

# Build this Dockerfile with the repository root as the build context:
#   docker build -f backend/Dockerfile .
#
# The reminder scheduler imports the workflow package at runtime, so the
# production image must include both backend/ and workflow/.
COPY backend/requirements.txt backend/requirements.txt
COPY workflow/requirements.txt workflow/requirements.txt
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r backend/requirements.txt -r workflow/requirements.txt

COPY backend/ backend/
COPY workflow/ workflow/

ENV PYTHONPATH=/app/backend:/app

WORKDIR /app/backend

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
