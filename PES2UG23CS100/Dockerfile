# Use a lightweight Python image
FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /app

# Copy dependencies and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY app.py .

# Create a directory for our "Simulated Block Volume"
RUN mkdir -p /mnt/block_volume

# Expose the Flask port
EXPOSE 5000

# Run the application
CMD ["python", "app.py"]
