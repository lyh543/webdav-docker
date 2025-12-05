FROM alpine:3.19

# Install nginx and nginx-dav-ext-module
RUN apk add --no-cache \
    nginx \
    nginx-mod-http-dav-ext \
    apache2-utils \
    && mkdir -p /var/www/webdav \
    && mkdir -p /run/nginx

# Copy configuration files
COPY nginx.conf /etc/nginx/nginx.conf
COPY entrypoint.sh /entrypoint.sh

# Set permissions
RUN chmod +x /entrypoint.sh \
    && chown -R nginx:nginx /var/www/webdav \
    && chmod 755 /var/www/webdav

# Volume for WebDAV data
VOLUME ["/var/www/webdav"]

ENTRYPOINT ["/entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]
