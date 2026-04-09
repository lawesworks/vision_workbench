from fastapi import APIRouter, Request
from app.services.tunnel_manager import start_tunnel, stop_tunnel, get_tunnel_status

router = APIRouter()


@router.post("/tunnel/start")
def tunnel_start(request: Request):
    return start_tunnel(request.app)


@router.post("/tunnel/stop")
def tunnel_stop(request: Request):
    return stop_tunnel(request.app)


@router.get("/tunnel/status")
def tunnel_status(request: Request):
    return get_tunnel_status(request.app)