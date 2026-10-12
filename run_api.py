"""
FastAPI Server Launcher
Starts Uvicorn server for the AI Recruitment Platform REST API.
"""

import sys
import uvicorn
from src.config import get_settings

if __name__ == "__main__":
    settings = get_settings()
    print(f"🚀 Starting {settings.PROJECT_NAME} v{settings.VERSION} on http://localhost:8000")
    print("📖 Swagger UI Docs: http://localhost:8000/docs")
    print("📖 ReDoc Docs:      http://localhost:8000/redoc")
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
