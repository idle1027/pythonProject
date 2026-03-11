from fastapi import FastAPI
from pydantic import BaseModel
import uuid
import threading
from config.config import TASK_QUEUE
from app.worker import worker
from database.db import engine, SessionLocal
from database.models import Base, Task

# 创建数据库表
Base.metadata.create_all(bind=engine)

app = FastAPI()

# 请求模型
class CodeRequest(BaseModel):
    user_id: str
    code: str

# 启动 worker
@app.on_event("startup")
def start_workers():
    print("Starting workers...")
    for i in range(3):
        t = threading.Thread(target=worker, args=(i,), daemon=True)
        t.start()
    print("Workers started")

# 提交任务
@app.post("/run")
def run_code_api(request: CodeRequest):
    task_id = str(uuid.uuid4())

    db = SessionLocal()
    task = Task(task_id=task_id, user_id=request.user_id, status="waiting", result="")
    db.add(task)
    db.commit()
    db.close()

    TASK_QUEUE.put({"task_id": task_id, "user_id": request.user_id, "code": request.code})

    return {"task_id": task_id, "status": "waiting"}

# 查询任务结果
@app.get("/result/{task_id}")
def get_result(task_id: str):
    db = SessionLocal()
    task = db.query(Task).filter(Task.task_id == task_id).first()
    db.close()

    if task:
        return {"task_id": task.task_id, "user_id": task.user_id, "status": task.status, "result": task.result}
    return {"error": "task not found"}

# 查看所有任务
@app.get("/tasks")
def get_all_tasks():
    db = SessionLocal()
    tasks = db.query(Task).all()
    db.close()
    result = [{"task_id": t.task_id, "user_id": t.user_id, "status": t.status, "result": t.result} for t in tasks]
    return {"total": len(result), "tasks": result}

# 健康检查接口
@app.get("/health")
def health():
    return {"status": "ok"}