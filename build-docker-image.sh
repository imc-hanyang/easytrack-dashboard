source .env
DOCKER_DEFAULT_PLATFORM=linux/amd64 docker build . -t qobiljon/dashboard-geoplan:${DASHBOARD_IMG_VER}
