#!/bin/sh

# Default credentials if not provided
WEBDAV_USERNAME=${WEBDAV_USERNAME:-admin}
WEBDAV_PASSWORD=${WEBDAV_PASSWORD:-admin}
PUID=${PUID:-1000}
PGID=${PGID:-1000}
PORT=${PORT:-80}

# Remove default nginx user/group created during image build
deluser nginx 2>/dev/null || true
delgroup nginx 2>/dev/null || true

# Handle GID - check if group exists, create if not
EXISTING_GROUP=$(getent group "$PGID" | cut -d: -f1)
if [ -n "$EXISTING_GROUP" ]; then
    NGINX_GROUP="$EXISTING_GROUP"
    echo "Using existing group: $NGINX_GROUP (GID = $PGID)"
else
    addgroup -g $PGID nginx
    NGINX_GROUP="nginx"
    echo "Created group: nginx (GID = $PGID)"
fi

# Handle UID - check if user exists, create if not
EXISTING_USER=$(getent passwd "$PUID" | cut -d: -f1)
if [ -n "$EXISTING_USER" ]; then
    NGINX_USER="$EXISTING_USER"
    echo "Using existing user: $NGINX_USER (UID = $PUID)"
else
    adduser -D -H -u $PUID -G "$NGINX_GROUP" -s /sbin/nologin nginx
    NGINX_USER="nginx"
    echo "Created user: nginx (UID = $PUID, GID = $PGID)"
fi

# Update nginx user in config - handle both user and group
# Format: "user username groupname;" or "user username;"
sed -i "1s/^user .*;/user $NGINX_USER $NGINX_GROUP;/" /etc/nginx/nginx.conf

# Update nginx port in config
sed -i "s/listen 80;/listen $PORT;/" /etc/nginx/nginx.conf

# Always regenerate htpasswd file on startup
echo "Creating htpasswd file for user: $WEBDAV_USERNAME"
htpasswd -bc /etc/nginx/.htpasswd "$WEBDAV_USERNAME" "$WEBDAV_PASSWORD"

echo "Starting WebDAV server with Nginx..."
echo "Nginx user: $NGINX_USER (UID:GID = $PUID:$PGID)"
echo "Port: $PORT"
echo "WebDAV username: $WEBDAV_USERNAME"
echo "WebDAV URL: http://localhost:$PORT/webdav"

exec "$@"
