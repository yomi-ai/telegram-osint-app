FROM python:3.10-slim

# Set the working directory
WORKDIR /app

# Install system dependencies required for Poetry
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry using the official installer
RUN curl -sSL https://install.python-poetry.org | python3 -

# Add Poetry to PATH
ENV PATH="/root/.local/bin:$PATH"

# Copy only the pyproject.toml and poetry.lock to leverage Docker cache
COPY pyproject.toml poetry.lock /app/

# Configure Poetry to not create a virtual environment
RUN poetry config virtualenvs.create false

# Install dependencies
RUN poetry install --no-interaction --no-ansi

# Copy the rest of the application code
COPY . /app

# Expose the application port (optional)
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "src.app_module:http_server", "--host", "0.0.0.0", "--port", "8000"]
