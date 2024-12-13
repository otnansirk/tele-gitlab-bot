# Use a lightweight Python base image
FROM python:3.10-slim

# Set environment variables to prevent Python from writing .pyc files and buffering stdout
ENV PYTHONUNBUFFERED 1

# Set a working directory in the container
WORKDIR /app

# Copy the requirements file first to leverage Docker's cache
COPY requirements.txt /app/

# Install dependencies (FastAPI, Uvicorn, etc.)
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . /app/

# Expose the port Uvicorn will run on
EXPOSE 8000

# Run the FastAPI app with Uvicorn (this will be the command when the container starts)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
