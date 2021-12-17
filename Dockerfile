FROM python
ENV CASSANDRA_PORT 9072
RUN mkdir /home/et_dashboard
COPY . /home/et_dashboard
WORKDIR /home/et_dashboard
RUN pip install -r requirements.txt
RUN python manage.py makemigrations
RUN python manage.py migrate
EXPOSE 80 443
CMD ["python", "manage.py", "runserver", "0:80"]
