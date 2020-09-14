```shell script
celery -A tasks worker -l info -Q judge –n worker@judge
```