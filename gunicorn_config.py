import multiprocessing
import dotenv
from os import getenv

dotenv.load_dotenv()

bind = f'{getenv("APP_HOST")}:{getenv("APP_PORT")}'
max_requests = 1000
workers = multiprocessing.cpu_count() * 2 + 1
