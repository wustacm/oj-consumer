
- 从RabbitMQ的队列judge中获取判题任务，运行之后，保存到result队列中
- 如果需要判题的任务没有测试数据，就需要通过系统后台的API接口去获得数据
- 如果判题机和后台条件允许的话，可以使用容器的目录映射实现判题数据共享

---

```shell script
celery -A tasks worker -l info -Q judge –n worker@judge
```
