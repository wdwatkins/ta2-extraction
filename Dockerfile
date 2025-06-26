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
