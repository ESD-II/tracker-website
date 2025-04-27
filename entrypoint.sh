#!/bin/sh

# Exit on error
set -e

echo "Waiting for MySQL..."
# Use nc (netcat) or wait-for-it.sh to wait for the database if needed
# This requires installing netcat in the Dockerfile: apt-get install -y netcat-traditional
while ! nc -z tracker_mysql 3306; do
  sleep 1
done
echo "MySQL started"

# Apply database migrations
echo "Applying database migrations..."
python manage.py migrate --noinput

# Start Supervisor to manage Daphne and MQTT Bridge
echo "Starting supervisord..."
exec supervisord -c /app/backend/config/supervisord.conf
# Make sure the path to supervisord.conf is correct