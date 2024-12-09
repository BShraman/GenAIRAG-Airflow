#!/bin/bash

# Create the user if it doesn't already exist
if ! airflow users list | grep -q 'admin'; then
    echo "Creating the admin user..."
    airflow users create \
        --username admin \
        --firstname Admin \
        --lastname User \
        --email admin@example.com \
        --role Admin \
        --password admin
fi

# Initialize the Airflow database if not already initialized
if [ ! -f ${AIRFLOW_HOME}/airflow.db ]; then
    echo "Initializing Airflow database..."
    airflow db init
fi

# Check if the user has provided an argument for a specific Airflow command
# If no argument is provided, default to starting the webserver
if [ "$1" = "webserver" ]; then
    echo "Starting Airflow webserver..."
    exec airflow webserver

elif [ "$1" = "scheduler" ]; then
    echo "Starting Airflow scheduler..."
    exec airflow scheduler

elif [ "$1" = "worker" ]; then
    echo "Starting Airflow worker..."
    exec airflow celery worker

elif [ "$1" = "init" ]; then
    echo "Initializing Airflow DB..."
    exec airflow db init

else
    echo "Unknown command: $1"
    echo "Available commands: webserver, scheduler, worker, init"
    exit 1
fi