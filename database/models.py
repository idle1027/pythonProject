from sqlalchemy import Column, String, Text
from database.db import Base


class Task(Base):
    __tablename__ = "tasks"

    task_id = Column(String, primary_key=True, index=True)
    user_id = Column(String, index=True)
    status = Column(String)
    result = Column(Text)