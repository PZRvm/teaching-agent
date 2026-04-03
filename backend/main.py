import uvicorn
from fastapi import FastAPI

from models.user import router as user_router

app = FastAPI()

app.include_router(user_router)

@app.get("/")
async def root():
    return {"message": "Hello Bigger Applications!"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
