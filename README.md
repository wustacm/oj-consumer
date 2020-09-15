```shell script
celery -A tasks worker -l info -Q judge –n worker@judge
```

```shell script
flake8 --ignore=E722,W504 --exclude=venv,migrations,__pycache__ --max-line-length=120 .
```