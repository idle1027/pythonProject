import subprocess
import uuid
import os
import json


def execute_code(code, timeout=10):

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
                "--cpus=1",
                "--memory=256m",
                "-v",
                f"{os.getcwd()}/runtime:/app",
                "python:3.10-alpine",
                "python",
                f"/app/{file_id}.py"
            ],
            capture_output=True,
            text=True,
            timeout=timeout
        )

        # 构建结构化的执行结果
        execution_result = {
            "status": "success",
            "stdout": result.stdout,
            "stderr": result.stderr,
            "return_code": result.returncode
        }

        return json.dumps(execution_result, ensure_ascii=False)

    except subprocess.TimeoutExpired:
        # 超时处理
        execution_result = {
            "status": "timeout",
            "error": f"Execution timeout after {timeout} seconds",
            "timeout": timeout
        }
        return json.dumps(execution_result, ensure_ascii=False)

    except FileNotFoundError:
        # Docker未安装或未运行
        execution_result = {
            "status": "error",
            "error": "Docker is not available. Please ensure Docker is installed and running."
        }
        return json.dumps(execution_result, ensure_ascii=False)

    except Exception as e:
        # 其他错误
        execution_result = {
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