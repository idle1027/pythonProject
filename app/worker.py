import time
from config.config import TASK_QUEUE, USER_RUNNING_COUNT, MAX_USER_CONCURRENT
from app.executor import execute_code
from database.db import SessionLocal
from database.models import Task


def worker(worker_id):
    while True:
        if not TASK_QUEUE.empty():
            task = TASK_QUEUE.get()
            task_id = task["task_id"]
            user_id = task["user_id"]
            code = task["code"]

            if user_id not in USER_RUNNING_COUNT:
                USER_RUNNING_COUNT[user_id] = 0

            # 如果用户任务超过限制
            if USER_RUNNING_COUNT[user_id] >= MAX_USER_CONCURRENT:
                TASK_QUEUE.put(task)
                time.sleep(1)
                continue

            USER_RUNNING_COUNT[user_id] += 1

            db = SessionLocal()

            db_task = db.query(Task).filter(Task.task_id == task_id).first()

            if db_task:
                db_task.status = "running"
                db.commit()

            print(f"[Worker {worker_id}] running task {task_id}")

            result = execute_code(code)

            print(f"[Worker {worker_id}] finished task {task_id}")

            if db_task:
                db_task.status = "finished"
                db_task.result = result
                db.commit()

            db.close()

            USER_RUNNING_COUNT[user_id] -= 1
        else:
            time.sleep(1)