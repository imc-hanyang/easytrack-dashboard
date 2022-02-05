# base image
FROM python:3.7-slim

# environment variables
ENV CASSANDRA_HOST 10.10.2.7
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# set working directory
RUN mkdir /home/et_dashboard
COPY . /home/et_dashboard
WORKDIR /home/et_dashboard

# install dependencies
RUN pip install -r requirements.txt
RUN pip install django-extensions Werkzeug
RUN pip install pyOpenSSL
RUN python manage.py makemigrations
RUN python manage.py migrate

# open ports
EXPOSE 80 443

# run web server
 CMD ["python", "manage.py", "runserver_plus", "--cert-file", "cert.pem", "--key-file", "key.pem"]
# CMD ["python", "manage.py", "runserver", "0:80"]