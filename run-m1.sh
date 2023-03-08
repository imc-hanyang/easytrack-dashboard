# Description: Run docker-compose on M1 Mac

# Load environment variables
set -a
source .env
set +a

# Simulate linux/amd64 platform
# (due to SCRAM auth issue with psycopg2 and libpq-dev)
DOCKER_DEFAULT_PLATFORM=linux/amd64 docker-compose up -d
