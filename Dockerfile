# Use an official Python base image
FROM python:3.9-slim

# Set environment variable to enable unbuffered output
ENV PYTHONUNBUFFERED=1

# Install necessary dependencies, including rclone
RUN apt-get update && apt-get install -y \
    curl unzip git \
    && curl https://rclone.org/install.sh | bash

# Set the working directory in the container
WORKDIR /app

# Copy the necessary files to the container
COPY main.py /app/main.py
COPY requirements.txt /app/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Define the entry point to run the script
ENTRYPOINT ["python", "main.py"]
