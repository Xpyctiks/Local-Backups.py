bind = "127.0.0.1:8000"
workers = 2
threads = 4
worker_class = "gthread"
wsgi_app = "webapp:application"
accesslog = "-"
errorlog = "-"
