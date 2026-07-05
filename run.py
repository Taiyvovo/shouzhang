"""一键启动手账编辑器"""
import subprocess, sys, time, webbrowser, os
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def kill_port(port: int) -> None:
    try:
        result = subprocess.run(
            f'netstat -ano | findstr :{port}',
            capture_output=True, text=True, shell=True, timeout=5,
        )
        for line in result.stdout.splitlines():
            parts = line.strip().split()
            if len(parts) >= 5 and "LISTENING" in line:
                pid = parts[-1]
                subprocess.run(f"taskkill /PID {pid} /F", capture_output=True, shell=True)
    except Exception:
        pass


print("=" * 40)
print("  手账编辑器 v0.1")
print("  启动中...")
print("=" * 40)
print()

kill_port(8000)
kill_port(5173)
time.sleep(1)

api = subprocess.Popen(
    [sys.executable, "-m", "uvicorn", "server:app", "--host", "127.0.0.1", "--port", "8000"],
    cwd=str(ROOT),
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
)

frontend = subprocess.Popen(
    "npx.cmd vite --host 127.0.0.1",
    cwd=str(ROOT / "editor"),
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
    shell=True,
)

time.sleep(5)

if api.poll() is not None:
    print("[X] 后端启动失败")
    print("    请检查：pip install fastapi uvicorn")
    print("    手动测试：python -m uvicorn server:app --host 127.0.0.1 --port 8000")
    frontend.terminate()
    input("按任意键退出...")
    sys.exit(1)

if frontend.poll() is not None:
    print("[X] 前端启动失败")
    print("    请检查：cd editor && npm install")
    api.terminate()
    input("按任意键退出...")
    sys.exit(1)

url = "http://localhost:5173"
print(f"[OK] 后端 http://127.0.0.1:8000")
print(f"[OK] 前端 {url}")
print()
webbrowser.open(url)
print("浏览器已打开，按 Ctrl+C 停止所有服务")
print()

try:
    api.wait()
except KeyboardInterrupt:
    print()
    print("正在停止...")
    frontend.terminate()
    api.terminate()
    kill_port(8000)
    kill_port(5173)
    print("已停止，下次再见")
