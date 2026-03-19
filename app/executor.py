import subprocess
import uuid
import os
import json
from typing import Dict, Any
from config.config import DOCKER_IMAGE, DOCKER_CPU_LIMIT, DOCKER_MEMORY_LIMIT


def execute_code(code: str, timeout: int = 10) -> str:
    """
    在隔离的 Docker 容器中执行用户代码
    
    Args:
        code: 要执行的 Python 代码
        timeout: 超时时间（秒）
    
    Returns:
        JSON 格式的执行结果，包含状态、输出和错误信息
    
    安全特性:
        - --network=none: 禁止网络访问
        - --read-only: 只读文件系统
        - --security-opt=no-new-privileges: 防止权限提升
        - --cpus=1: 限制 CPU 使用
        - --memory=256m: 限制内存使用
    """
    file_id = str(uuid.uuid4())

    runtime_dir = "runtime"

    if not os.path.exists(runtime_dir):
        os.makedirs(runtime_dir)

    file_path = f"{runtime_dir}/{file_id}.py"

    with open(file_path, "w") as f:
        f.write(code)

    try:
        result = subprocess.run(
            [
                "docker",
                "run",
                "--rm",
                "--network=none",
                "--read-only",
                "--security-opt=no-new-privileges",
                "--cpus", DOCKER_CPU_LIMIT,
                "--memory", DOCKER_MEMORY_LIMIT,
                "-v",
                f"{os.getcwd()}/runtime:/app",
                DOCKER_IMAGE,
                "python",
                f"/app/{file_id}.py"
            ],
            capture_output=True,
            text=True,
            timeout=timeout
        )

        # 构建结构化的执行结果
        execution_result: Dict[str, Any] = {
            "status": "success",
            "stdout": result.stdout,
            "stderr": result.stderr,
            "return_code": result.returncode
        }

        return json.dumps(execution_result, ensure_ascii=False)

    except subprocess.TimeoutExpired:
        # 超时处理
        execution_result: Dict[str, Any] = {
            "status": "timeout",
            "error": f"Execution timeout after {timeout} seconds",
            "timeout": timeout
        }
        return json.dumps(execution_result, ensure_ascii=False)

    except FileNotFoundError:
        # Docker未安装或未运行
        execution_result: Dict[str, Any] = {
            "status": "error",
            "error": "Docker is not available. Please ensure Docker is installed and running."
        }
        return json.dumps(execution_result, ensure_ascii=False)

    except Exception as e:
        # 其他错误
        execution_result: Dict[str, Any] = {
            "status": "error",
            "error": str(e)
        }
        return json.dumps(execution_result, ensure_ascii=False)

    finally:
        # 清理临时文件
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"Error cleaning up temp file {file_path}: {e}")