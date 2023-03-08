FROM python:3.10-slim as base

# Housekeeping
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1


FROM base AS runtime-env-deps

# Configure libpq-dev linux dependency for psycopg2
# (PostgreSQL development library for python database driver)
RUN apt-get update
RUN apt-get install -y --no-install-recommends gcc
RUN apt-get install libpq-dev -y
ENV LDFLAGS '-L/usr/local/opt/libpq/lib'
ENV CPPFLAGS '-I/usr/local/opt/libpq/include'
ENV PKG_CONFIG_PATH '/usr/local/opt/libpq/lib/pkgconfig'

# Cook a python virtual environment
RUN pip install --upgrade pip
RUN pip install pipenv
COPY Pipfile .
RUN PIPENV_VENV_IN_PROJECT=1 pipenv install --deploy --skip-lock


FROM base AS runtime

# Linux user and workdir setup (for security and database access)
RUN useradd --create-home easytrack
WORKDIR /home/easytrack
USER easytrack

# Copy python runtime (pre-cooked virtual environment)
COPY --from=runtime-env-deps /.venv $HOME/.venv
ENV PATH="$HOME/.venv/bin:$PATH"

# Copy app files : django apps, static files, and launch script
COPY dashboard dashboard
COPY api api
COPY static static
COPY manage.py manage.py

# Expose port (app runs this port)
EXPOSE 8000

# Run Django app
ENTRYPOINT ["python", "manage.py"]
CMD ["runserver", "0:8000"]
