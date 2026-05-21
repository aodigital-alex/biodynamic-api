"""FastAPI application factory."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import router


def create_app() -> FastAPI:
    app = FastAPI(
        title="Biodynamic Calendar API",
        description="Open source REST API for biodynamic calendar calculations",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["GET"],
        allow_headers=["*"],
    )
    app.include_router(router)
    return app


app = create_app()


def main():
    import uvicorn
    uvicorn.run("biodynamic.api.app:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    main()
