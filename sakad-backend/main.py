from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.capture import router as capture_router
from routes.gallery import router as gallery_router
from routes.health import router as health_router
from routes.sessions import router as sessions_router

app = FastAPI(title="Sakad Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(capture_router)
app.include_router(gallery_router)
app.include_router(health_router)
app.include_router(sessions_router)


@app.get("/")
async def root():
    return {"status": "ok"}
