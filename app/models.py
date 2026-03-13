from pydantic import BaseModel
from typing import List, Optional


class Task(BaseModel):
    task_id: str
    code: str
    status: str = "pending"  # 任务状态：pending, running, completed


class User(BaseModel):
    user_id: str
    tasks: List[Task] = []  # 用户的所有任务