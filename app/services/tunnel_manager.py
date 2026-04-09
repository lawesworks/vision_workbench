import subprocess
import threading
import re
from fastapi import FastAPI


def init_tunnel_state(app: FastAPI):
    app.state.tunnel_process = None
    app.state.tunnel_url = None
    app.state.tunnel_running = False


def _capture_tunnel_url(app: FastAPI):
    process = app.state.tunnel_process
    if process is None or process.stdout is None:
        return

    for line in process.stdout:
        line = line.strip()
        print(f"[cloudflared] {line}")

        match = re.search(r"https://[-a-z0-9]+\.trycloudflare\.com", line)
        if match:
            app.state.tunnel_url = match.group(0)
            print(f"Tunnel URL captured: {app.state.tunnel_url}")
            break


def start_tunnel(app: FastAPI, local_url: str = "http://localhost:8000"):
    # Prevent duplicate tunnels
    existing = app.state.tunnel_process
    if existing is not None and existing.poll() is None:
        return {
            "status": "already_running",
            "url": app.state.tunnel_url
        }

    app.state.tunnel_url = None

    process = subprocess.Popen(
        ["cloudflared", "tunnel", "--url", local_url],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    app.state.tunnel_process = process
    app.state.tunnel_running = True

    thread = threading.Thread(
        target=_capture_tunnel_url,
        args=(app,),
        daemon=True
    )
    thread.start()

    return {
        "status": "starting",
        "url": None
    }


def stop_tunnel(app: FastAPI):
    process = app.state.tunnel_process

    if process is None or process.poll() is not None:
        app.state.tunnel_process = None
        app.state.tunnel_url = None
        app.state.tunnel_running = False
        return {"status": "not_running"}

    process.terminate()

    try:
        process.wait(timeout=5)
    except Exception:
        process.kill()

    app.state.tunnel_process = None
    app.state.tunnel_url = None
    app.state.tunnel_running = False

    return {"status": "stopped"}


def get_tunnel_status(app: FastAPI):
    process = app.state.tunnel_process
    running = process is not None and process.poll() is None

    return {
        "running": running,
        "url": app.state.tunnel_url,
        "pid": process.pid if running else None
    }