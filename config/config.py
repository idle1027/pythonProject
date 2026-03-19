import queue
import threading
import os
from dotenv import load_dotenv
from pathlib import Path

# 加载环境变量
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

# =========================
# 全局配置和共享状态
# =========================

# Worker 配置
WORKER_COUNT = int(os.getenv("WORKER_COUNT", "3"))  # Worker 数量
MAX_USER_CONCURRENT = int(os.getenv("MAX_USER_CONCURRENT", "5"))  # 每个用户最大并发任务数

# Docker 配置
DOCKER_IMAGE = os.getenv("DOCKER_IMAGE", "python:3.10-alpine")  # Docker 镜像
DOCKER_CPU_LIMIT = os.getenv("DOCKER_CPU_LIMIT", "1")  # CPU 限制
DOCKER_MEMORY_LIMIT = os.getenv("DOCKER_MEMORY_LIMIT", "256m")  # 内存限制

# 代码执行配置
MAX_CODE_SIZE = int(os.getenv("MAX_CODE_SIZE", "10240"))  # 最大代码大小（字节）
DEFAULT_TIMEOUT = int(os.getenv("DEFAULT_TIMEOUT", "10"))  # 默认超时时间（秒）
MAX_TIMEOUT = int(os.getenv("MAX_TIMEOUT", "300"))  # 最大超时时间（秒）

# 任务队列（优先队列，按优先级排序）
TASK_QUEUE = queue.PriorityQueue()

# 用户运行中的任务计数（字典，key为用户ID，value为运行中任务数）
USER_RUNNING_TASKS = {}

# Worker 状态（字典，key为worker_id，value为状态字符串）
WORKER_STATUS = {}

# 取消的任务集合（存储被请求取消但尚未执行完成的任务ID）
CANCELLED_TASKS = set()

# 线程锁，保护共享数据的并发访问
USER_RUNNING_TASKS_LOCK = threading.Lock()
WORKER_STATUS_LOCK = threading.Lock()
CANCELLED_TASKS_LOCK = threading.Lock()