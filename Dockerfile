# Use the official Python 3.9.2 image
FROM python:3.9.2-slim

# Set the working directory
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . /app/

ENV FLASK_APP=vigyazzhat-serv.py

# Expose the Flask app's port (default: 5000)
EXPOSE 5000

# Command to run the app
CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]