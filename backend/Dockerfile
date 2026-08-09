FROM python:3.11-slim

WORKDIR /app

# Install hatchling and other build dependencies
RUN pip install --no-cache-dir hatchling

# Copy project files
COPY . /app/

# Install the project
RUN pip install -e .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
