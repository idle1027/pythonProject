import subprocess
import uuid
import os


def execute_code(code, timeout=30):

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

        return result.stdout if result.stdout else result.stderr

    except subprocess.TimeoutExpired:
        return "Timeout"