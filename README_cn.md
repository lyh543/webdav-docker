# WebDAV Docker 镜像

[English](https://github.com/lyh543/webdav-docker/blob/master/README.md) | 简体中文 | [Docker Hub](https://hub.docker.com/r/lyh543/webdav)

[![Docker Image Version](https://img.shields.io/docker/v/lyh543/webdav/latest?label=lyh543/webdav&color=blue)](https://hub.docker.com/r/lyh543/webdav)
![Docker Image Size](https://img.shields.io/docker/image-size/lyh543/webdav/latest?label=Image%20Size&color=green)
![Docker Pulls](https://img.shields.io/docker/pulls/lyh543/webdav?label=Pulls&color=orange)

基于 Nginx 的轻量级 WebDAV 服务器。

## 快速开始

### 使用 Docker 命令

构建镜像：

```bash
docker build -t webdav .
```

运行容器：

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

## 配置选项

### 环境变量

- `WEBDAV_USERNAME`: WebDAV 登录用户名（默认：admin）
- `WEBDAV_PASSWORD`: WebDAV 登录密码（默认：admin）
- `PUID`: 运行 nginx 进程的用户 ID（默认：1000）
- `PGID`: 运行 nginx 进程的组 ID（默认：1000）
- `PORT`: 容器内部监听端口（默认：80）

### 端口

- 容器内部端口：`80`（可通过 `PORT` 环境变量修改）
- 映射到主机端口：`8080`（可在 docker-compose.yml 或 -p 参数中修改）

### 数据卷

- `/var/www/webdav`: WebDAV 数据存储目录

## 目录结构

```
webdav/
├── Dockerfile           # Docker 镜像定义
├── docker-compose.yml   # Docker Compose 配置
├── nginx.conf          # Nginx 配置
├── entrypoint.sh       # 启动脚本
├── data/               # WebDAV 数据目录（自动创建）
└── README.md           # 说明文档
```

## 使用技巧

### 设置正确的 UID/GID

为了避免文件权限问题，建议设置 `PUID` 和 `PGID` 为你的宿主机用户 ID：

```bash
# 查看当前用户的 UID 和 GID
id

# 在 docker-compose.yml 中设置
environment:
  - PUID=1000  # 替换为你的 UID
  - PGID=1000  # 替换为你的 GID
```

### 自定义端口

如需修改容器内部端口（例如在同一主机运行多个实例）：

```yaml
# docker-compose.yml
ports:
  - "8080:8080"  # 映射到自定义端口
environment:
  - PORT=8080    # 容器内部监听 8080
```
