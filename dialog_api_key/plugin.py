from http import HTTPStatus

from decouple import Csv, config
from fastapi import FastAPI, Request
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse


class Settings:
    @property
    def header(self):
        return config("DIALOG_API_KEY_HEADER", default="X-Api-Key")

    @property
    def allowed_api_keys(self):
        return config("DIALOG_API_KEYS", cast=Csv(post_process=set))

    @property
    def except_paths(self):
        return config(
            "DIALOG_API_KEY_IGNORE_PATHS",
            cast=Csv(post_process=set),
            default="/docs,/openapi.json",
        )


settings = Settings()


async def api_key_middleware(request: Request, call_next):
    if request.url.path in settings.except_paths:
        return await call_next(request)

    api_key = request.headers.get(settings.header)
    if not api_key or api_key not in settings.allowed_api_keys:
        return JSONResponse(
            {"detail": "Invalid API Key."},
            status_code=HTTPStatus.UNAUTHORIZED,
        )

    return await call_next(request)


def register_plugin(app: FastAPI):
    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema

        schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            summary=app.summary,
            routes=app.routes,
        )
        schema["components"]["securitySchemes"] = {
            "ApiKeyAuth": {
                "type": "apiKey",
                "in": "header",
                "name": settings.header,
            }
        }
        schema["security"] = [
            {"ApiKeyAuth": []},
        ]
        for path in settings.except_paths:
            try:
                schema["paths"][path]["security"] = []
            except KeyError:
                continue

        app.openapi_schema = schema
        return schema

    app.openapi = custom_openapi
    app.middleware("http")(api_key_middleware)
