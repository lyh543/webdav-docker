#!/bin/sh

# Default credentials if not provided
WEBDAV_USERNAME=${WEBDAV_USERNAME:-admin}
WEBDAV_PASSWORD=${WEBDAV_PASSWORD:-admin}
PUID=${PUID:-1000}
PGID=${PGID:-1000}
PORT=${PORT:-80}

# Update nginx user UID and GID
echo "Setting UID:GID to $PUID:$PGID"
deluser nginx 2>/dev/null || true
delgroup nginx 2>/dev/null || true
addgroup -g $PGID nginx
adduser -D -H -u $PUID -G nginx -s /sbin/nologin nginx

# Update nginx port in config
sed -i "s/listen 80;/listen $PORT;/" /etc/nginx/nginx.conf

# Always regenerate htpasswd file on startup
echo "Creating htpasswd file for user: $WEBDAV_USERNAME"
htpasswd -bc /etc/nginx/.htpasswd "$WEBDAV_USERNAME" "$WEBDAV_PASSWORD"

# Ensure proper permissions
chown -R nginx:nginx /var/www/webdav
chmod -R 755 /var/www/webdav

echo "Starting WebDAV server with Nginx..."
echo "Port: $PORT"
echo "Username: $WEBDAV_USERNAME"
echo "WebDAV URL: http://localhost:$PORT/webdav"

exec "$@"
