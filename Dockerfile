# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Gunicorn (ensure it's installed globally)
RUN pip install gunicorn

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Use Gunicorn with multiple worker processes for better performance
# The number of workers is generally recommended to be 2 * CPU + 1
# Replace 'app:app' with the appropriate entry point for your Flask application
CMD ["gunicorn", "--workers", "4", "--bind", "0.0.0.0:5000", "app:app"]

