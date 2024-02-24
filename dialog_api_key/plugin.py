from http import HTTPStatus

from decouple import Csv, config
from fastapi import FastAPI, Request
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
    app.middleware("http")(api_key_middleware)
