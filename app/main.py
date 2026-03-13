from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from datetime import datetime
import uuid
import threading
import traceback
import os

from config.config import TASK_QUEUE, WORKER_STATUS, CANCELLED_TASKS, CANCELLED_TASKS_LOCK
from app.worker import worker
from app.scheduler import scheduler

from database.db import engine, SessionLocal
from database.models import Base, Task

Base.metadata.create_all(bind=engine)

app = FastAPI()

print("FaaS System Started")


# =========================
# 根路径 - 返回前端页面
# =========================

@app.get("/")
async def read_root():
    html_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "faas-dashboard.html")
    return FileResponse(html_path)


# =========================
# 解决前端跨域问题
# =========================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================
# 请求模型
# =========================

class CodeRequest(BaseModel):

    user_id: str
    code: str
    priority: int = 5
    timeout: int = 10


# =========================
# 启动系统
# =========================

@app.on_event("startup")
def start_system():

    print("Starting scheduler")

    s = threading.Thread(target=scheduler, daemon=True)
    s.start()

    print("Starting workers")

    for i in range(3):

        t = threading.Thread(target=worker, args=(i,), daemon=True)

        t.start()

    print("System ready")


# =========================
# 提交任务
# =========================

@app.post("/run")
def run_code_api(request: CodeRequest):

    try:
        task_id = str(uuid.uuid4())

        db = SessionLocal()

        task = Task(

            task_id=task_id,
            user_id=request.user_id,
            status="waiting",
            result="",
            priority=request.priority,
            timeout=request.timeout

        )

        db.add(task)
        db.commit()
        db.close()

        TASK_QUEUE.put((request.priority, task_id, {

            "task_id": task_id,
            "user_id": request.user_id,
            "code": request.code

        }))

        return {

            "task_id": task_id,
            "status": "waiting"

        }

    except Exception as e:
        print(f"Error in run_code_api: {e}")
        traceback.print_exc()
        return {"error": str(e)}


# =========================
# 查询结果
# =========================

@app.get("/result/{task_id}")
def get_result(task_id: str):

    db = SessionLocal()

    task = db.query(Task).filter(Task.task_id == task_id).first()

    db.close()

    if task:

        return {

            "task_id": task.task_id,
            "user_id": task.user_id,
            "status": task.status,
            "result": task.result,
            "created_at": task.created_at.isoformat() if task.created_at else None,
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "finished_at": task.finished_at.isoformat() if task.finished_at else None,
            "execution_time": task.execution_time,
            "error_message": task.error_message,
            "timeout": task.timeout

        }

    return {"error": "task not found"}


# =========================
# 查看所有任务
# =========================

@app.get("/tasks")
def get_all_tasks():

    db = SessionLocal()

    tasks = db.query(Task).all()

    db.close()

    result = []

    for t in tasks:

        task_dict = {

            "task_id": t.task_id,
            "user_id": t.user_id,
            "status": t.status,
            "priority": t.priority,
            "result": t.result,
            "created_at": t.created_at.isoformat() if t.created_at else None,
            "started_at": t.started_at.isoformat() if t.started_at else None,
            "finished_at": t.finished_at.isoformat() if t.finished_at else None,
            "execution_time": t.execution_time,
            "error_message": t.error_message,
            "timeout": t.timeout

        }

        result.append(task_dict)

    return {

        "total": len(result),
        "tasks": result

    }


# =========================
# worker状态
# =========================

@app.get("/workers")
def workers():

    return WORKER_STATUS


# =========================
# 健康检查
# =========================

@app.get("/health")
def health():

    return {"status": "ok"}


# =========================
# 清除已完成任务
# =========================

@app.delete("/clear-finished")
def clear_finished_tasks():

    db = SessionLocal()

    deleted = db.query(Task).filter(Task.status == "finished").delete()

    db.commit()

    db.close()

    return {

        "message": "Cleared finished tasks",
        "deleted_count": deleted

    }


# =========================
# 取消任务
# =========================

@app.post("/cancel/{task_id}")
def cancel_task(task_id: str):

    db = SessionLocal()

    task = db.query(Task).filter(Task.task_id == task_id).first()

    if not task:
        db.close()
        return {"error": "task not found"}

    # 如果任务在waiting状态，直接标记为取消
    if task.status == "waiting":
        task.status = "cancelled"
        task.finished_at = datetime.utcnow()
        db.commit()
        db.close()
        return {"message": "Task cancelled", "task_id": task_id}

    # 如果任务在running状态，添加到取消集合中，worker会检查并取消
    if task.status == "running":
        with CANCELLED_TASKS_LOCK:
            CANCELLED_TASKS.add(task_id)
        db.close()
        return {"message": "Task cancellation requested", "task_id": task_id}

    # 其他状态（finished, failed, cancelled, timeout）
    db.close()
    return {"error": f"Cannot cancel task with status: {task.status}"}