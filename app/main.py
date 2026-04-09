from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from fastapi.responses import FileResponse

from app.routers.ui import router as ui_router
from app.routers.ui_image import router as ui_image_router
from app.routers.ui_url import router as ui_url_router
from app.routers.ui_video import router as ui_video_router
from app.routers.api_image import router as api_image_router
from app.routers.api_url import router as api_url_router
from app.routers.api_video import router as api_video_router
from app.routers.stream import router as stream_router
from app.routers.model_config import router as model_config_router
from app.routers.tunnel import router as tunnel_router
from app.routers.upload_model import router as upload_model_router



from app.services.tunnel_manager import init_tunnel_state

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI()

# Initiation Cloudflare state
init_tunnel_state(app)


from fastapi.middleware.cors import CORSMiddleware
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://console.armada.ai",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse(Path("app/static/favicon.ico"))

app.include_router(ui_router)
app.include_router(ui_image_router)
app.include_router(ui_url_router)
app.include_router(ui_video_router)
app.include_router(api_image_router)
app.include_router(api_url_router)
app.include_router(api_video_router)
app.include_router(stream_router)
app.include_router(model_config_router)
app.include_router(tunnel_router)
app.include_router(upload_model_router)