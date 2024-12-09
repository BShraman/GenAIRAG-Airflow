# Use the official Apache Airflow image as the base image
FROM apache/airflow:2.10.3

# Set environment variables
ENV AIRFLOW_HOME=/opt/airflow

# Switch to root to install packages
USER root

# Install system dependencies for building Python packages
RUN apt-get update && \
    apt-get install -y build-essential libpq-dev vim

# Upgrade pip and setuptools
RUN pip3 install --upgrade pip setuptools

# Install Python dependencies
COPY requirements.txt ${AIRFLOW_HOME}/requirements.txt
RUN pip3 install -r ${AIRFLOW_HOME}/requirements.txt

# Create necessary directories for DAGs, logs, and plugins
RUN mkdir -p ${AIRFLOW_HOME}/dags && \
    mkdir -p ${AIRFLOW_HOME}/logs && \
    mkdir -p ${AIRFLOW_HOME}/plugins

# Set the working directory to AIRFLOW_HOME
WORKDIR ${AIRFLOW_HOME}

# Copy the custom entrypoint script into the image
COPY scripts/entrypoint.sh ${AIRFLOW_HOME}/entrypoint.sh

# Give execution permissions to the entrypoint script
RUN chmod +x ${AIRFLOW_HOME}/entrypoint.sh

# Expose the port for the Airflow webserver
EXPOSE 8080 7860

# Set the entrypoint to the custom entrypoint script
ENTRYPOINT ["tail", "-f", "/dev/null"]
