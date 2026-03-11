import threading
import time
from config.config import TASK_QUEUE, USER_TASKS
from app.executor import execute_code

def worker(worker_id):
    while True:
        if not TASK_QUEUE.empty():
            task = TASK_QUEUE.get()
            task_id = task["task_id"]
            code = task["code"]

            print(f"[Worker {worker_id}] 执行任务: {task_id}")

            USER_TASKS[task_id]["status"] = "running"

            result = execute_code(code)

            USER_TASKS[task_id]["status"] = "finished"
            USER_TASKS[task_id]["result"] = result

        time.sleep(0.5)


def start_workers(num_workers=3):
    for i in range(num_workers):
        t = threading.Thread(target=worker, args=(i,), daemon=True)
        t.start()