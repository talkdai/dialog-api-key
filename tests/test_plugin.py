from http import HTTPStatus
from unittest import mock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from dialog_api_key.plugin import Settings, register_plugin

app = FastAPI()
register_plugin(app)


@app.get("/")
async def view():
    return "OK"


VALID_API_KEY = "dialog"

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_settings():
    with mock.patch.object(Settings, "allowed_api_keys", {VALID_API_KEY}):
        yield


def test_valid_api_key():
    response = client.get("/", headers={"X-Api-Key": VALID_API_KEY})
    assert response.status_code == HTTPStatus.OK


def test_invalid_api_key():
    response = client.get("/", headers={"X-Api-Key": "invalid_key"})
    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_ignored_path():
    response = client.get("/docs")
    assert response.status_code == HTTPStatus.OK
