import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 加载.env文件
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

# MySQL数据库配置
# 优先使用 Railway 不自动覆盖的变量名
MYSQL_HOST = os.getenv("RAILWAY_MYSQL_HOST") or os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = os.getenv("RAILWAY_MYSQL_PORT") or os.getenv("MYSQL_PORT", "3306")
MYSQL_USER = os.getenv("RAILWAY_MYSQL_USER") or os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("RAILWAY_MYSQL_PASSWORD") or os.getenv("MYSQL_PASSWORD", "")
MYSQL_DATABASE = os.getenv("RAILWAY_MYSQL_DATABASE") or os.getenv("MYSQL_DATABASE", "faas_system")

# 调试输出：打印实际使用的环境变量值
print(f"Database Config:")
print(f"  RAILWAY_MYSQL_HOST = {os.getenv('RAILWAY_MYSQL_HOST')}")
print(f"  MYSQL_HOST = {os.getenv('MYSQL_HOST')}")
print(f"  Using MYSQL_HOST = {MYSQL_HOST}")
print(f"  MYSQL_PORT = {MYSQL_PORT}")
print(f"  MYSQL_USER = {MYSQL_USER}")
print(f"  MYSQL_DATABASE = {MYSQL_DATABASE}")

DATABASE_URL = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"

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