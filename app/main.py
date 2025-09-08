from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from .config import settings
from .db import init_db
from .api.routes import messages


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name, version="1.0.0")

    # init DB
    @app.on_event("startup")
    def _startup():
        init_db()

    # Uniform error shape for HTTPExceptions
    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        # Let FastAPI handle HTTPException and validation errors natively
        from fastapi.exceptions import HTTPException
        from pydantic_core import ValidationError
        if isinstance(exc, HTTPException):
            # Wrap into the error envelope if detail is dict with our structure
            if isinstance(exc.detail, dict):
                return JSONResponse(status_code=exc.status_code, content={"status": "error", "error": exc.detail})
            else:
                return JSONResponse(status_code=exc.status_code, content={
                    "status": "error",
                    "error": {"code": "HTTP_ERROR", "message": str(exc.detail)},
                })
        if isinstance(exc, ValidationError):
            return JSONResponse(status_code=422, content={
                "status": "error",
                "error": {"code": "VALIDATION_ERROR", "message": "Entrada inválida", "details": str(exc)},
            })
        # Fallback
        return JSONResponse(status_code=500, content={
            "status": "error",
            "error": {"code": "SERVER_ERROR", "message": "Error inesperado"},
        })

    # Routes
    app.include_router(messages.router, prefix=settings.api_prefix)

    @app.get("/health", tags=["system"])
    def health():
        return {"status": "ok"}

    return app


app = create_app()
