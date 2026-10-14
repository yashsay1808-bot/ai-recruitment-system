"""
Routers package initialization.
"""

from api.routers.jobs import router as jobs_router
from api.routers.resumes import router as resumes_router
from api.routers.screenings import router as screenings_router
from api.routers.audits import router as audits_router
from api.routers.auth import router as auth_router
from api.routers.candidates import router as candidates_router

__all__ = [
    "jobs_router",
    "resumes_router",
    "screenings_router",
    "audits_router",
    "auth_router",
    "candidates_router",
]
