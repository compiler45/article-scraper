from celery import Celery


app = Celery('tasks',
             backend='redis://localhost:6379',
             broker='amqp://',
             include='tasks.tasks')

app.conf.update(worker_send_task_events=True)

if __name__ == "__main__":
    app.start()
