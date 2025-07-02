# Use the Python 3.12 slim image
FROM python:3.12-slim

# Set environment variables to optimize Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies (if needed for your packages)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Add DOI CA to local CAs so that SSL can work over VPN
COPY DOIRootCA2.crt /usr/local/share/ca-certificates

RUN chmod 644 /usr/local/share/ca-certificates/DOIRootCA2.crt && \
    update-ca-certificates

ENV PIP_CERT="/etc/ssl/certs/ca-certificates.crt" \
    SSL_CERT_FILE="/etc/ssl/certs/ca-certificates.crt" \
    CURL_CA_BUNDLE="/etc/ssl/certs/ca-certificates.crt" \
    REQUESTS_CA_BUNDLE="/etc/ssl/certs/ca-certificates.crt" \
    AWS_CA_BUNDLE="/etc/ssl/certs/ca-certificates.crt" \
    IN_CONTAINER="True"

# Copy dependency file first to leverage Docker layer caching
COPY requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# install cdr_schemas
RUN git clone https://github.com/DARPA-CRITICALMAAS/cdr_schemas &&\
    cd cdr_schemas && \
    poetry build -f sdist && \
    pip install dist/cdr_schemas-0.4.18.tar.gz && \
    cd ../ && rm -rf cdr_schemas
    

# Copy the rest of the application code
COPY . .

# Set the default command to run the pipeline
CMD ["python", "-m", "extraction_package.pipeline"]
