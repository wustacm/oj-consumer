import os

# debug log
DDLCW_DEBUG = os.getenv('DDLCW_DEBUG', 'False') == 'True'
# enable test cases sync
DDLCW_ENABLE_SYNC = os.getenv('DDLCW_SYNC_ENABLE', 'False') == 'True'
# is development or production
DDLCW_ENV = os.getenv('DDLCW_ENV', 'host')
# request test cases token
JUDGE_TOKEN = os.getenv('JUDGE_TOKEN', 'JUDGE_TOKEN')

# celery broker url
BROKER_URL = os.getenv('BROKER_URL', 'amqp://guest:guest@127.0.0.1:5672/')
# celery request data url
BACKEND_URL = os.getenv('BACKEND_URL', 'http://127.0.0.1') + '/api/problem/{problem_id}/sync_test_cases/'
