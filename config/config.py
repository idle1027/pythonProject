from queue import Queue

# 任务队列
TASK_QUEUE = Queue()

# 用户正在运行的任务数量S
USER_RUNNING_COUNT = {}

# 每个用户最大并发任务数
MAX_USER_CONCURRENT = 2