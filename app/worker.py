import time
from datetime import datetime

from config.config import (TASK_QUEUE, USER_RUNNING_TASKS, MAX_USER_CONCURRENT,
                          WORKER_STATUS, USER_RUNNING_TASKS_LOCK, WORKER_STATUS_LOCK,
                          CANCELLED_TASKS, CANCELLED_TASKS_LOCK)

from app.executor import execute_code

from database.db import SessionLocal
from database.models import Task


def worker(worker_id: int) -> None:
    """
    Worker 线程函数，从任务队列中获取并执行任务
    
    Args:
        worker_id: Worker 的唯一标识符
    """
    print(f"Worker {worker_id} started")

    with WORKER_STATUS_LOCK:
        WORKER_STATUS[worker_id] = "idle"

    while True:

        task = TASK_QUEUE.get()

        priority, task_id, task_data = task
        user_id = task_data["user_id"]
        code = task_data["code"]

        # 标记是否真正处理了任务（而不是重新入队）
        task_processed = False
        execution_start_time = None

        try:
            # 使用锁保护用户并发检查和计数更新，确保原子性
            with USER_RUNNING_TASKS_LOCK:
                if user_id not in USER_RUNNING_TASKS:
                    USER_RUNNING_TASKS[user_id] = 0

                if USER_RUNNING_TASKS[user_id] >= MAX_USER_CONCURRENT:
                    # 达到并发限制，重新入队
                    TASK_QUEUE.put((priority, task_id, task_data))
                    # 睡眠避免忙等待和活锁
                    time.sleep(0.5)
                    # 没有真正处理任务，不标记task_processed
                    continue

                # 原子性地增加计数
                USER_RUNNING_TASKS[user_id] += 1
                # 标记为已开始处理
                task_processed = True

            # 更新worker状态
            with WORKER_STATUS_LOCK:
                WORKER_STATUS[worker_id] = f"running {task_id}"

            # 记录开始执行时间
            execution_start_time = datetime.utcnow()

            db = SessionLocal()

            db_task = db.query(Task).filter(Task.task_id == task_id).first()

            if db_task:
                db_task.status = "running"
                db_task.started_at = execution_start_time
                db.commit()

            # 检查任务是否被取消
            with CANCELLED_TASKS_LOCK:
                if task_id in CANCELLED_TASKS:
                    CANCELLED_TASKS.remove(task_id)
                    if db_task:
                        execution_end_time = datetime.utcnow()
                        execution_time = (execution_end_time - execution_start_time).total_seconds()
                        db_task.status = "cancelled"
                        db_task.finished_at = execution_end_time
                        db_task.execution_time = execution_time
                        db.commit()
                    db.close()
                    print(f"Worker {worker_id}: Task {task_id} was cancelled")
                    continue

            # 执行代码，使用数据库中配置的超时时间
            timeout = db_task.timeout if db_task else 10
            result = execute_code(code, timeout=timeout)

            execution_end_time = datetime.utcnow()
            execution_time = (execution_end_time - execution_start_time).total_seconds()

            db_task = db.query(Task).filter(Task.task_id == task_id).first()

            if db_task:
                db_task.status = "finished"
                db_task.result = result
                db_task.finished_at = execution_end_time
                db_task.execution_time = execution_time
                db.commit()

            db.close()

            print(f"Worker {worker_id} finished task {task_id} in {execution_time:.2f}s")

        except Exception as e:
            print(f"Worker {worker_id} error processing task {task_id}: {e}")
            import traceback
            traceback.print_exc()

            # 记录错误信息到数据库
            if task_processed:
                try:
                    db = SessionLocal()
                    db_task = db.query(Task).filter(Task.task_id == task_id).first()

                    if db_task:
                        execution_end_time = datetime.utcnow()
                        execution_time = 0
                        if execution_start_time:
                            execution_time = (execution_end_time - execution_start_time).total_seconds()

                        db_task.status = "failed"
                        db_task.error_message = str(e)
                        db_task.finished_at = execution_end_time
                        db_task.execution_time = execution_time
                        db.commit()

                    db.close()
                except Exception as db_error:
                    print(f"Error updating task status in database: {db_error}")

        finally:
            # 只有真正处理了任务才需要清理
            if task_processed:
                # 使用锁保护计数减少
                with USER_RUNNING_TASKS_LOCK:
                    if user_id in USER_RUNNING_TASKS:
                        USER_RUNNING_TASKS[user_id] -= 1

                with WORKER_STATUS_LOCK:
                    WORKER_STATUS[worker_id] = "idle"

            # 标记任务处理完成
            TASK_QUEUE.task_done()