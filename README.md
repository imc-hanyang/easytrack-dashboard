# How to launch Easytrack dashboard with Docker

### Requirements
- Python 3.10
- Docker
- Docker-compose

### Launching the dashboard
- Clone the repository
- Go to the root of the repository
- Create ```.env``` file with the following content:
   - Django development server settings
      - ```DEBUG``` - deployment mode (```True``` or ```False```)
      - ```SERVERNAMES``` - which domain names the dashboard will be available on
      - ```INTERNAL_IPS``` - IP addresses that display debug toolbar
   - Database credentials
      - ```POSTGRES_HOST``` - database host
      - ```POSTGRES_PORT``` - database port
      - ```POSTGRES_DBNAME``` - database name
      - ```POSTGRES_TEST_DBNAME``` - database name for tests
      - ```POSTGRES_USER``` - database user
      - ```POSTGRES_PASSWORD``` - database password
   - Google API credentials
      - ```GOOGLE_API_KEY``` - Google API key (for Google oAuth2)
      - ```GOOGLE_CLIENT_ID``` - Google client ID (for Google oAuth2)
   - Django social auth credentials
      - ```SOCIAL_AUTH_GOOGLE_OAUTH2_KEY``` - Google client ID (for Google oAuth2)
      - ```SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET``` - Google client secret (for Google oAuth2)
   - Django secret key
      - ```DJANGO_SECRET_KEY``` - Django secret key (Django setting)
   - Easytrack test account details
      - ```TEST_ACCOUNT_EMAIL``` - Email of test account (app user)
      - ```TEST_ACCOUNT_NAME``` - Name of test account (app user)
- Launch the dashboard (build and run containers)
   - Linux
      ```bash
      docker-compose up -d
      ```
   - Apple M1
      ```bash
      DOCKER_DEFAULT_PLATFORM=linux/amd64 docker-compose up -d
      ```
      This is due to SCRAM authentication problem on recent versions of libpq-dev that is used by the psycopg2 database driver (a dependency of dashboard app).
