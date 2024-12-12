FROM apache/airflow:2.10.3

# Switch to root to install system dependencies
USER root

# Install system dependencies for Selenium (if required)
RUN apt-get update && apt-get install -y \
    python3-pip \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Chrome with driver
# FROM --platform=linux/amd64 python:3.8
# WORKDIR /home/airflow
# RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
# RUN echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list
# RUN apt-get update && apt-get install -y google-chrome-stable


# Switch back to airflow user
USER airflow

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your parser program into the container
COPY src/parser/data_parser.py /home/airflow/parser/
COPY src/parser/parser.py /home/airflow/parser/
COPY src/parser/tools.py /home/airflow/parser/

ENV PYTHONPATH "${PYTHONPATH}:/home/airflow/parser/"
