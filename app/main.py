from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from pydantic import BaseModel
from datetime import datetime
import uuid
import threading
import traceback
import os

from config.config import (TASK_QUEUE, WORKER_STATUS, CANCELLED_TASKS, CANCELLED_TASKS_LOCK,
                          WORKER_COUNT, MAX_CODE_SIZE, MAX_TIMEOUT)
from app.worker import worker
from app.scheduler import scheduler

from database.db import engine, SessionLocal
from database.models import Base, Task

Base.metadata.create_all(bind=engine)

app = FastAPI()

print("FaaS System Started")


# =========================
# 统一错误处理中间件
# =========================

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    """处理值错误（如输入验证失败）"""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"error": str(exc), "detail": "Invalid input parameter"}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """处理所有未捕获的异常"""
    print(f"Unhandled exception: {type(exc).__name__}: {exc}")
    traceback.print_exc()
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "Internal server error", "detail": str(exc)}
    )


# =========================
# 根路径 - 返回前端页面
# =========================

@app.get("/")
async def read_root() -> FileResponse:
    """返回前端仪表板页面"""
    html_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "faas-dashboard.html")
    return FileResponse(html_path)


# =========================
# 解决前端跨域问题
# =========================

# 从环境变量读取允许的来源，如果没有设置则允许所有（开发环境）
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",") if os.getenv("CORS_ORIGINS") else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================
# 请求模型
# =========================

class CodeRequest(BaseModel):
    """
    代码执行请求模型
    
    Attributes:
        user_id: 用户ID（必填，1-100字符）
        code: 要执行的Python代码（必填，最大10KB）
        priority: 任务优先级（1-10，默认5）
        timeout: 超时时间（秒，默认10，最大300）
    """
    user_id: str
    code: str
    priority: int = 5
    timeout: int = 10

    def validate(self) -> None:
        """
        验证请求参数的合法性
        
        Raises:
            ValueError: 当参数不合法时抛出异常
        """
        # 验证 user_id
        if not self.user_id:
            raise ValueError("user_id is required")
        if not isinstance(self.user_id, str):
            raise ValueError("user_id must be a string")
        if len(self.user_id) < 1 or len(self.user_id) > 100:
            raise ValueError("user_id must be between 1 and 100 characters")
        if not self.user_id.replace('_', '').replace('-', '').isalnum():
            raise ValueError("user_id can only contain alphanumeric characters, underscores, and hyphens")

        # 验证 code
        if not self.code:
            raise ValueError("code is required")
        if len(self.code.encode('utf-8')) > MAX_CODE_SIZE:
            raise ValueError(f"code size exceeds {MAX_CODE_SIZE} bytes limit")

        # 验证 priority
        if not isinstance(self.priority, int):
            raise ValueError("priority must be an integer")
        if self.priority < 1 or self.priority > 10:
            raise ValueError("priority must be between 1 and 10")

        # 验证 timeout
        if not isinstance(self.timeout, int):
            raise ValueError("timeout must be an integer")
        if self.timeout < 1 or self.timeout > MAX_TIMEOUT:
            raise ValueError(f"timeout must be between 1 and {MAX_TIMEOUT} seconds")


# =========================
# 启动系统
# =========================

@app.on_event("startup")
def start_system() -> None:
    """启动调度器和 Worker 线程池"""
    print("Starting scheduler")

    s = threading.Thread(target=scheduler, daemon=True)
    s.start()

    print(f"Starting {WORKER_COUNT} workers")

    for i in range(WORKER_COUNT):

        t = threading.Thread(target=worker, args=(i,), daemon=True)

        t.start()

    print("System ready")


# =========================
# 提交任务
# =========================

@app.post("/run")
def run_code_api(request: CodeRequest) -> dict:
    """
    提交代码执行任务
    
    Args:
        request: 包含用户ID、代码、优先级和超时时间的请求
    
    Returns:
        包含任务ID和状态的字典
    """
    try:
        # 验证输入参数
        request.validate()

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
def get_result(task_id: str) -> dict:
    """
    查询任务执行结果
    
    Args:
        task_id: 任务ID
    
    Returns:
        包含任务详细信息的字典
    """
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
def get_all_tasks() -> dict:
    """
    查询所有任务
    
    Returns:
        包含任务总数和任务列表的字典
    """
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
def workers() -> dict:
    """获取所有 Worker 的状态"""
    return WORKER_STATUS


# =========================
# 健康检查
# =========================

@app.get("/health")
def health() -> dict:
    """
    健康检查接口

    Returns:
        包含系统健康状态的字典
    """
    health_status = {
        "status": "healthy",
        "checks": {
            "database": "unknown",
            "docker": "unknown",
            "workers": "unknown"
        }
    }

    try:
        # 检查数据库连接
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        health_status["checks"]["database"] = "connected"
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["checks"]["database"] = f"failed: {str(e)}"

    try:
        # 检查 Docker 可用性
        import subprocess
        result = subprocess.run(
            ["docker", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            health_status["checks"]["docker"] = "available"
        else:
            health_status["checks"]["docker"] = "not_available"
    except Exception as e:
        health_status["checks"]["docker"] = f"failed: {str(e)}"

    try:
        # 检查 Worker 状态
        from config.config import WORKER_STATUS
        active_workers = len([w for w in WORKER_STATUS.values() if w != "idle"])
        health_status["checks"]["workers"] = f"{len(WORKER_STATUS)} workers, {active_workers} active"
    except Exception as e:
        health_status["checks"]["workers"] = f"failed: {str(e)}"

    # 如果有任何检查失败，标记为不健康
    if any("failed" in str(check) for check in health_status["checks"].values()):
        health_status["status"] = "unhealthy"

    return health_status


# =========================
# 清除已完成任务
# =========================

@app.delete("/clear-finished")
def clear_finished_tasks() -> dict:
    """
    清除所有已完成的任务
    
    Returns:
        包含删除数量的字典
    """
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
def cancel_task(task_id: str) -> dict:
    """
    取消指定任务
    
    Args:
        task_id: 任务ID
    
    Returns:
        包含操作结果的字典
    """
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