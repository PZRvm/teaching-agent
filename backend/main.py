from dotenv import load_dotenv

load_dotenv()  # noqa: E402

import uvicorn  # noqa: E402
from fastapi import FastAPI  # noqa: E402

from models.checkpoint.router import router as checkpoint_router  # noqa: E402
from models.observation.router import router as observation_router  # noqa: E402
from models.session.router import router as session_router  # noqa: E402
from models.session.router_websocket import router as websocket_router  # noqa: E402

app = FastAPI()

app.include_router(checkpoint_router)
app.include_router(observation_router)
app.include_router(session_router)
app.include_router(websocket_router)


@app.get("/")
async def root():
    return {"message": "Hello Bigger Applications!"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
