from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.auth.router import router as auth_router
from backend.schema.router import router as schema_router
from backend.history.router import router as history_router
from backend.mcp.router import router as mcp_router
from backend.agent.router import router as chat_router

app = FastAPI(
    title="SQL Assistant API",
    description="AI-powered SQL assistant backend",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8501",
        "http://127.0.0.1:8501"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(schema_router)
app.include_router(history_router)
app.include_router(mcp_router)
app.include_router(chat_router)

@app.get("/")
def root():
    return {
        "status": "running",
        "app": "SQL Assistant API",
        "version": "1.0.0"
    }