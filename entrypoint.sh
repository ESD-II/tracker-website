#!/bin/sh

# Exit immediately if a command exits with a non-zero status.
set -e

echo "Waiting for MySQL..."
# This loop waits for the MySQL service (named tracker_mysql) to be reachable on port 3306
# Requires netcat (nc) to be installed in the Django container (see Dockerfile modification below)
while ! nc -z tracker_mysql 3306; do
  echo "Waiting for MySQL..."
  sleep 1
done
echo "MySQL started"

# Run database migrations if necessary
echo "Building database migrations..."
python manage.py makemigrations

# Apply database migrations
echo "Applying database migrations..."
# Assumes manage.py is in the WORKDIR (/app)
python manage.py migrate --noinput
echo "Migrations applied."

# Start Supervisor to manage Daphne and MQTT Bridge
echo "Starting supervisord..."
# Ensure the path to the config file is correct relative to WORKDIR (/app)
exec supervisord -c /app/config/supervisord.conf