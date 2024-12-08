FROM python:3.12

ENV PYTHONUNBUFFERED True

# Combine update, install, and clean up
RUN apt-get update && apt-get install -y build-essential libpq-dev && apt-get clean && rm -rf /var/lib/apt/lists/*

# First copy the requirements.txt and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Set the application directory

WORKDIR /

# Copy the rest of the application
COPY . .

# CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
ENTRYPOINT ["python3", "main.py"]
