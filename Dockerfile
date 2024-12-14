# Use a base Python image
FROM python:3.9

# Set working directory
WORKDIR /app

# Copy application files
COPY . /app

# Install dependencies
RUN pip install pymongo

# Expose ports
EXPOSE 3000 5000

# Start the application
CMD ["python", "main.py"]
