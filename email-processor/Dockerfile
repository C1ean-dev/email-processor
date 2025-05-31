# Use an official Python runtime as a parent image
FROM python:3.9-slim-buster

# Install Tesseract-OCR and Poppler-utils
RUN apt-get update && \
    apt-get install -y tesseract-ocr poppler-utils && \
    rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Install any needed packages specified in requirements.txt
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the port the app runs on (Cloud Run expects 8080 by default)
EXPOSE 8080

# Define environment variable for Flask
ENV FLASK_APP=app.py

# Run the application with Gunicorn, binding to the PORT environment variable provided by Cloud Run
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8080", "app:app"]
