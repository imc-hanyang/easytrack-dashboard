## run docker
#export $(cat .env | xargs)
#docker build . -t dashboard
#docker run dashboard -p 80:80 -d

# run local gunicorn
gunicorn -c gunicorn_config.py dashboard.wsgi
