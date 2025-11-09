# Use the official Python lightweight image
FROM python:3.13-slim

# Install the project into /app
COPY . /app
WORKDIR /app

# Allow statements and log messages to immediately appear in the logs
ENV PYTHONUNBUFFERED=1

# Copy requirements if you have one, else skip this step
COPY requirements.txt ./

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE $PORT

# Run the flask app (new)
CMD ["python", "agent.py"]