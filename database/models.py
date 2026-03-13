from sqlalchemy import Column, String, Text, Integer, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Task(Base):

    __tablename__ = "tasks"

    task_id = Column(String(36), primary_key=True)  # UUID格式

    user_id = Column(String(100))  # 用户ID

    status = Column(String(20))  # waiting, running, finished, failed, cancelled, timeout

    result = Column(Text)

    priority = Column(Integer)

    # FaaS执行监控字段
    created_at = Column(DateTime, default=datetime.utcnow)  # 任务创建时间
    started_at = Column(DateTime)  # 开始执行时间
    finished_at = Column(DateTime)  # 完成时间
    execution_time = Column(Float)  # 执行耗时（秒）
    error_message = Column(Text)  # 错误信息
    timeout = Column(Integer, default=10)  # 超时设置（秒）