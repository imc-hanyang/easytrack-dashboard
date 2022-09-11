set -a
source .env
set +a

./run-static-server.sh
pipenv run gunicorn dashboard.wsgi -c gunicorn.ini
