FROM alpine:latest

# Set any ENV values you need (for example):
#ENV API_KEY=""
#ENV API_SECRET=""

# Install system dependencies
RUN apk add --no-cache bash python3 py3-pip

# Create and activate a virtual environment
RUN python3 -m venv /venv
ENV PATH="/venv/bin:$PATH"

# Copy requirements and install inside the venv
COPY requirements.txt /app/requirements.txt
WORKDIR /app
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy your main script
COPY rebalancer.py /app/rebalancer.py

# Use the venv's Python as the entry point
ENTRYPOINT [ "python3", "/app/rebalancer.py" ]
