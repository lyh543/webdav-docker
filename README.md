# WebDAV Docker Image

English | [简体中文](https://github.com/lyh543/webdav-docker/blob/master/README_cn.md) | [Docker Hub](https://hub.docker.com/r/lyh543/webdav)

[![Docker Image Version](https://img.shields.io/docker/v/lyh543/webdav/latest?label=lyh543/webdav&color=blue)](https://hub.docker.com/r/lyh543/webdav)
![Docker Image Size](https://img.shields.io/docker/image-size/lyh543/webdav/latest?label=Image%20Size&color=green)
![Docker Pulls](https://img.shields.io/docker/pulls/lyh543/webdav?label=Pulls&color=orange)

A lightweight WebDAV server based on Nginx.

## Quick Start

### Using Docker Command

Build the image:

```bash
docker build -t webdav .
```

Run the container:

```bash
docker run -d \
  --name webdav \
  -p 8080:80 \
  -e WEBDAV_USERNAME=admin \
  -e WEBDAV_PASSWORD=admin123 \
  -e PUID=$UID \
  -e PGID=$GID \
  -e PORT=80 \
  -v $(pwd)/data:/var/www/webdav \
  lyh543/webdav
```

## Configuration Options

### Environment Variables

- `WEBDAV_USERNAME`: WebDAV login username (default: admin)
- `WEBDAV_PASSWORD`: WebDAV login password (default: admin)
- `PUID`: User ID for nginx process (default: 1000)
- `PGID`: Group ID for nginx process (default: 1000)
- `PORT`: Internal container listening port (default: 80)

### Ports

- Internal container port: `80` (configurable via `PORT` environment variable)
- Host port mapping: `8080` (configurable in docker-compose.yml or -p parameter)

### Volumes

- `/var/www/webdav`: WebDAV data storage directory

## Directory Structure

```
webdav/
├── Dockerfile           # Docker image definition
├── docker-compose.yml   # Docker Compose configuration
├── nginx.conf          # Nginx configuration
├── entrypoint.sh       # Startup script
├── data/               # WebDAV data directory (auto-created)
└── README.md           # Documentation
```

## Usage Tips

### Setting Correct UID/GID

To avoid file permission issues, it's recommended to set `PUID` and `PGID` to your host user ID:

```bash
# Check your current user's UID and GID
id

# Set in docker-compose.yml
environment:
  - PUID=1000  # Replace with your UID
  - PGID=1000  # Replace with your GID
```

### Custom Port

To modify the internal container port (e.g., running multiple instances on the same host):

```yaml
# docker-compose.yml
ports:
  - "8080:8080"  # Map to custom port
environment:
  - PORT=8080    # Container listens on 8080
```
