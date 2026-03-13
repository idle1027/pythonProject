"""
数据库初始化脚本
用于创建MySQL数据库和表结构
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

# 加载.env文件
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)

# MySQL配置
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "faas_system")

def create_database():
    """创建数据库"""
    try:
        # 连接到MySQL服务器（不指定数据库）
        root_url = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}"
        engine = create_engine(root_url)

        with engine.connect() as conn:
            # 创建数据库
            conn.execute(text(f"CREATE DATABASE IF NOT EXISTS {MYSQL_DATABASE} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
            print(f"数据库 {MYSQL_DATABASE} 创建成功")

    except OperationalError as e:
        print(f"创建数据库失败: {e}")
        print("请检查MySQL连接配置和用户权限")
        raise

def create_tables():
    """创建表结构"""
    try:
        from database.db import engine
        from database.models import Base

        # 创建所有表
        Base.metadata.create_all(bind=engine)
        print("表结构创建成功")

    except Exception as e:
        print(f"创建表结构失败: {e}")
        raise

if __name__ == "__main__":
    print("开始初始化数据库...")
    create_database()
    create_tables()
    print("数据库初始化完成！")