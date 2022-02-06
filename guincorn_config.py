command = 'python -m gunicorn'
bind = '0.0.0.0:443'
certfile = 'cert.pem'
keyfile = 'key.pem'
workers = 5
