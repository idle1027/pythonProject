import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 加载.env文件
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

# MySQL数据库配置
# 支持自定义变量，同时兼容 Railway 自动提供的变量
MYSQL_HOST = os.getenv("MYSQL_HOST") or os.getenv("MYSQLHOST", "localhost")
MYSQL_PORT = os.getenv("MYSQL_PORT") or os.getenv("MYSQLPORT", "3306")
MYSQL_USER = os.getenv("MYSQL_USER") or os.getenv("MYSQLUSER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD") or os.getenv("MYSQLPASSWORD", "")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE") or os.getenv("MYSQLDATABASE", "faas_system")

DATABASE_URL = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"

# 打印数据库配置用于调试（密码已脱敏）
print("=" * 50)
print("DATABASE CONFIGURATION:")
print(f"HOST: {MYSQL_HOST}")
print(f"PORT: {MYSQL_PORT}")
print(f"USER: {MYSQL_USER}")
print(f"DATABASE: {MYSQL_DATABASE}")
# 不打印完整URL，仅打印脱敏信息
print(f"URL: mysql+pymysql://{MYSQL_USER}:***@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}")
print("=" * 50)

engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)