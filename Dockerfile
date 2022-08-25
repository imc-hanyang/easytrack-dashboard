# base image
FROM python:3.9-slim

# environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# set working directory
RUN useradd --create-home easytrack
WORKDIR /home/easytrack
USER easytrack
COPY . .

# install dependencies
RUN pip install -r requirements.txt
RUN pip install gunicorn
# RUN pip install pyOpenSSL
RUN python manage.py makemigrations
RUN python manage.py migrate

# open ports
EXPOSE 80

# run web server
CMD ["python", "manage.py", "runserver", "0:80"]
#CMD ["gunicorn", "-c", "gunicorn_config.py", "dashboard.wsgi"]
