# Use an official Python runtime as a parent image
FROM python:3.12

# Set work directory
WORKDIR /app

# Copy project files into the container
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Accept Binance API key and secret as build arguments
ARG BINANCE_API_KEY
ARG BINANCE_API_SECRET

# Set them as environment variables
ENV BINANCE_API_KEY=$BINANCE_API_KEY
ENV BINANCE_API_SECRET=$BINANCE_API_SECRET

# Expose the Flask application port
EXPOSE 54321

# Run your application
CMD ["python", "app.py"]