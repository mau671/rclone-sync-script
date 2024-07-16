# Use an official Python base image
FROM python:3.9-slim

# Set environment variable to enable unbuffered output
ENV PYTHONUNBUFFERED=1

# Install necessary dependencies, including rclone
RUN apt-get update && apt-get install -y \
    curl \
    && curl https://rclone.org/install.sh | bash \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Copy the necessary files to the container
COPY distribute.py /app/main.py
COPY rclone.conf /app/rclone.conf
COPY requirements.txt /app/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Define the entry point to run the script
ENTRYPOINT ["python", "main.py"]
