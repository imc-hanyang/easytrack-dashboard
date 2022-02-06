command = 'python -m gunicorn'
bind = '0.0.0.0:443'
certfile = 'fullchain.pem'
keyfile = 'privkey.pem'
workers = 5
