import queue
import threading

# 任务队列
TASK_QUEUE = queue.PriorityQueue()

# 每个用户最大并发（提高到5以避免测试时达到限制）
MAX_USER_CONCURRENT = 5

# 用户运行中的任务
USER_RUNNING_TASKS = {}

# worker状态
WORKER_STATUS = {}

# 取消的任务集合
CANCELLED_TASKS = set()

# 线程锁保护共享数据
USER_RUNNING_TASKS_LOCK = threading.Lock()
WORKER_STATUS_LOCK = threading.Lock()
CANCELLED_TASKS_LOCK = threading.Lock()