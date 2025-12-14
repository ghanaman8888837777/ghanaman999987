# Use the full, standard Python 3.11 image (includes build tools)
FROM python:3.11

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies required by psycopg2
RUN apt-get update && apt-get install -y libpq-dev

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code into the container
COPY . .

# Set the entrypoint to run your listener script
# NOTE: The Procfile will override this if running the 'web' process
ENTRYPOINT ["python", "run_listener.py"]