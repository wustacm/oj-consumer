import os

# debug log
DDLCW_DEBUG = os.getenv('DDLCW_DEBUG', 'False') == 'True'
# enable test cases sync
DDLCW_ENABLE_SYNC = os.getenv('DDLCW_SYNC_ENABLE', 'False') == 'True'
# is development or production
DDLCW_ENV = os.getenv('DDLCW_ENV', 'development')
# request test cases token
JUDGE_TOKEN = os.getenv('JUDGE_TOKEN', 'JUDGE_TOKEN')
# RabbitMQ host
RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', '127.0.0.1')
# RabbitMQ port
RABBITMQ_PORT = os.getenv('RABBITMQ_PORT', 5672)
# RabbitMQ user
RABBITMQ_USER = os.getenv('RABBITMQ_USER', 'guest')
# RabbitMQ user password
RABBITMQ_PASS = os.getenv('RABBITMQ_PASS', 'guest')
# BACKEND protocol
BACKEND_PROTOCOL = os.getenv('BACKEND_PROTOCOL', 'http')
# BACKEND host
BACKEND_HOST = os.getenv('BACKEND_PROTOCOL', '127.0.0.1')
# BACKEND port
BACKEND_PORT = os.getenv('BACKEND_PROTOCOL', 8000)
