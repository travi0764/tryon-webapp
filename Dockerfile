# Use the official Python image
FROM python:3.11-slim

# Create and set the working directory
WORKDIR /app

# Copy the requirements file to the working directory
COPY requirements.txt .

# Upgrade pip and setuptools
RUN pip install --upgrade pip setuptools

# Install dependencies from requirements.txt
RUN pip install -r requirements.txt

# Copy the application code to the container
COPY . .

# Expose the port that your Flask application will run on
EXPOSE 8080

# Command to run the application
CMD ["flask", "run", "--host=0.0.0.0", "--port=8080"]
