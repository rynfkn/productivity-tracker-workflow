FROM python:3.12-slim

WORKDIR /app

# Install backend + workflow dependencies
COPY backend/requirements.txt backend/requirements.txt
COPY workflow/requirements.txt workflow/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt -r workflow/requirements.txt

# Copy source
COPY backend/ backend/
COPY workflow/ workflow/

# backend/app uses relative imports (from app.*),
# and the scheduler imports workflow/ from the project root.
# PYTHONPATH covers both.
ENV PYTHONPATH=/app/backend:/app

WORKDIR /app/backend

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
