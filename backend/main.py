from dotenv import load_dotenv

load_dotenv()  # noqa: E402

import uvicorn  # noqa: E402
from fastapi import FastAPI  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402

from core.settings import CORS_ALLOW_HEADERS, CORS_ALLOW_METHODS, CORS_ALLOW_ORIGINS  # noqa: E402
from models.checkpoint.router import router as checkpoint_router  # noqa: E402
from models.observation.router import router as observation_router  # noqa: E402
from models.session.router import router as session_router  # noqa: E402
from models.session.router_websocket import router as websocket_router  # noqa: E402

app = FastAPI()

# CORS 配置（从 configs/app.yml 读取）
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=CORS_ALLOW_METHODS,
    allow_headers=CORS_ALLOW_HEADERS,
)

app.include_router(checkpoint_router)
app.include_router(observation_router)
app.include_router(session_router)
app.include_router(websocket_router)


@app.get("/")
async def root():
    return {"message": "Hello Bigger Applications!"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
