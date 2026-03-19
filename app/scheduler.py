import time

from config.config import (TASK_QUEUE, USER_RUNNING_TASKS, MAX_USER_CONCURRENT,
                          WORKER_STATUS, USER_RUNNING_TASKS_LOCK, WORKER_STATUS_LOCK)


def scheduler() -> None:
    """
    调度器函数，定期检查系统状态并输出监控信息
    
    每5秒检查一次任务队列、Worker状态和用户并发情况
    """
    print("Scheduler started")

    while True:

        time.sleep(5)  # 每5秒检查一次系统状态

        with USER_RUNNING_TASKS_LOCK:
            with WORKER_STATUS_LOCK:
                # 打印系统状态，用于监控和调试
                print(f"Scheduler Report - Queue size: {TASK_QUEUE.qsize()}, "
                      f"Running tasks: {sum(USER_RUNNING_TASKS.values())}, "
                      f"Workers: {WORKER_STATUS}")

                # 检查是否有用户长时间达到并发限制，可能导致任务饿死
                # 这里可以添加更复杂的调度策略
                for user_id, running_count in USER_RUNNING_TASKS.items():
                    if running_count >= MAX_USER_CONCURRENT:
                        print(f"Warning: User {user_id} at max concurrency ({running_count})")

                # 检查空闲worker数量
                idle_workers = sum(1 for status in WORKER_STATUS.values()
                                 if status == "idle")
                if idle_workers == 0 and TASK_QUEUE.qsize() > 0:
                    print("Warning: All workers busy but tasks in queue")