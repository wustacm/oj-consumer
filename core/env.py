import os

# debug log
OJ_DEBUG = os.getenv('OJ_DEBUG', 'False') == 'True'
# enable test cases sync
OJ_ENABLE_SYNC = os.getenv('OJ_SYNC_ENABLE', 'False') == 'True'
# is development or production
OJ_ENV = os.getenv('OJ_ENV', 'host')
# request test cases token
JUDGE_TOKEN = os.getenv('JUDGE_TOKEN', 'JUDGE_TOKEN')

# celery broker url
BROKER_URL = os.getenv('BROKER_URL', 'amqp://guest:guest@127.0.0.1:5672/')
# celery request data url
BACKEND_URL = os.getenv('BACKEND_URL', 'http://127.0.0.1') + '/api/problem/{problem_id}/sync_test_cases/'
