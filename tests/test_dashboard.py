import asyncio
import io
import json

import httpx
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from opentrons_ai.app import PASSWORDS, create_app
from opentrons_ai.robot import CameraError, Robot
from opentrons_ai.storage import utc_now


def jpeg():
    output = io.BytesIO()
    Image.new("RGB", (64, 48), "green").save(output, format="JPEG")
    return output.getvalue()


class FakeRobot:
    capture_error = None

    async def status(self):
        return {
            "connected": True,
            "pipettes": {
                "left": {
                    "name": "p300_multi_gen2",
                    "model": "p300_multi_v2.1",
                    "id": "test-serial",
                },
                "right": {"name": None, "model": None, "id": None},
            },
            "health": {"name": "test", "api_version": "26.6.0"},
            "camera": {"cameraEnabled": True},
        }

    async def capture(self):
        if self.capture_error:
            raise CameraError(self.capture_error)
        return jpeg(), (64, 48)


@pytest.fixture
def console(tmp_path):
    robot = FakeRobot()
    app = create_app(tmp_path, robot=robot, secure_cookie=False)
    with app.state.store.connect() as db:
        for name, role in (("admin", "admin"), ("viewer", "viewer"), ("operator", "operator")):
            db.execute(
                "INSERT INTO users VALUES (?, ?, ?, ?)",
                (
                    name,
                    PASSWORDS.hash("correct-test-password"),
                    role,
                    utc_now(),
                ),
            )
    with TestClient(app) as client:
        client.headers["X-Requested-With"] = "opentrons-console"
        yield client, app, robot


def login(client, username="admin"):
    result = client.post(
        "/api/v1/login",
        json={
            "username": username,
            "password": "correct-test-password",
        },
    )
    assert result.status_code == 200
    client.headers["X-CSRF-Token"] = result.json()["csrf"]
    return result


def test_authentication_and_csrf(console):
    client, _, _ = console
    for path in ("robot", "hardware", "captures", "users", "audit"):
        assert client.get(f"/api/v1/{path}").status_code == 401
    result = login(client)
    assert "HttpOnly" in result.headers["set-cookie"]
    assert "SameSite=strict" in result.headers["set-cookie"]
    del client.headers["X-CSRF-Token"]
    assert client.post("/api/v1/captures").status_code == 403
    client.headers["X-CSRF-Token"] = result.json()["csrf"]
    assert client.post("/api/v1/logout").status_code == 200
    assert client.get("/api/v1/me").status_code == 401


def test_login_rate_limit_and_generic_errors(console):
    client, _, _ = console
    for _ in range(10):
        response = client.post("/api/v1/login", json={"username": "missing", "password": "wrong"})
        assert response.json()["detail"] == "login_failed"
    assert (
        client.post("/api/v1/login", json={"username": "admin", "password": "wrong"}).status_code
        == 429
    )


def test_mutations_require_same_origin_header(console):
    client, _, _ = console
    del client.headers["X-Requested-With"]
    assert (
        client.post("/api/v1/login", json={"username": "admin", "password": "x"}).status_code == 403
    )


@pytest.mark.parametrize("username", ["viewer", "operator"])
def test_catalog_and_account_changes_are_admin_only(console, username):
    client, _, _ = console
    login(client, username)
    assert client.get("/api/v1/hardware").status_code == 200
    assert (
        client.post("/api/v1/hardware", json={"name": "plate", "category": "labware"}).status_code
        == 403
    )
    assert client.post("/api/v1/hardware/discover").status_code == 403
    assert client.get("/api/v1/users").status_code == 403
    if username == "viewer":
        assert client.post("/api/v1/captures").status_code == 403


def test_hardware_import_is_atomic_and_approval_uses_revision(console):
    client, _, _ = console
    login(client)
    assert (
        client.post(
            "/api/v1/hardware/import",
            json={
                "items": [
                    {"name": "plate", "category": "labware"},
                    {"name": "bad", "category": "invalid"},
                ]
            },
        ).status_code
        == 422
    )
    assert client.get("/api/v1/hardware").json() == []
    imported = client.post(
        "/api/v1/hardware/import",
        json={
            "items": [
                {"name": "测试 plate", "category": "labware"},
            ]
        },
    )
    assert imported.status_code == 201
    record = client.get("/api/v1/hardware").json()[0]
    assert record["status"] == "pending"
    endpoint = f"/api/v1/hardware/{record['id']}/approve"
    assert client.post(endpoint, json={"revision": 999}).status_code == 409
    assert client.post(endpoint, json={"revision": 1}).status_code == 200
    assert client.post(endpoint, json={"revision": 1}).status_code == 409
    assert client.get("/api/v1/hardware").json()[0]["approved_by"] == "admin"


def test_import_does_not_allow_self_approval_or_bad_definitions(console):
    client, _, _ = console
    login(client)
    assert (
        client.post(
            "/api/v1/hardware",
            json={
                "name": "plate",
                "category": "labware",
                "status": "approved",
            },
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/api/v1/hardware",
            json={
                "name": "plate",
                "category": "labware",
                "definition": {"schemaVersion": 2},
            },
        ).status_code
        == 422
    )


def test_discovery_is_idempotent_and_never_approves(console):
    client, _, _ = console
    login(client)
    assert len(client.post("/api/v1/hardware/discover").json()["ids"]) == 1
    assert client.post("/api/v1/hardware/discover").json()["ids"] == []
    assert client.get("/api/v1/hardware").json()[0]["status"] == "pending"


def test_camera_files_require_login_and_failure_does_not_change_catalog(console):
    client, _, robot = console
    login(client, "operator")
    photo = client.post("/api/v1/captures")
    assert photo.status_code == 201
    path = f"/api/v1/captures/{photo.json()['id']}/image"
    assert client.get(path).content == jpeg()
    robot.capture_error = "camera_disabled"
    assert client.post("/api/v1/captures").json()["detail"] == "camera_disabled"
    assert len(client.get("/api/v1/captures").json()) == 1
    assert client.get("/api/v1/hardware").json() == []
    assert client.get("/api/v1/robot").status_code == 200
    client.cookies.clear()
    assert client.get(path).status_code == 401


def test_account_creation_and_hardware_persist(console, tmp_path):
    client, _, _ = console
    login(client)
    assert (
        client.post(
            "/api/v1/users",
            json={
                "username": "colleague",
                "password": "long-unique-password",
                "role": "viewer",
            },
        ).status_code
        == 201
    )
    client.post("/api/v1/hardware", json={"name": "persisted", "category": "other"})
    restored = create_app(tmp_path, robot=FakeRobot(), secure_cookie=False)
    assert restored.state.store.hardware()[0]["name"] == "persisted"
    with restored.state.store.connect() as db:
        assert (
            db.execute("SELECT role FROM users WHERE username='colleague'").fetchone()[0]
            == "viewer"
        )


def test_no_experiment_or_arbitrary_robot_control_routes(console):
    client, _, _ = console
    login(client)
    for route in ("runs", "robot/home", "robot/move", "robot/proxy", "camera/enable"):
        assert client.post(f"/api/v1/{route}", json={}).status_code in (404, 405)


def test_robot_adapter_uses_only_observation_and_picture_endpoints():
    calls = []

    def handler(request):
        calls.append((request.method, request.url.path))
        assert request.headers["opentrons-version"] == "2"
        if request.url.path == "/camera/picture":
            return httpx.Response(200, content=jpeg(), headers={"Content-Type": "image/jpg"})
        return httpx.Response(200, json={})

    robot = Robot("http://robot")
    robot.client = lambda timeout=5: httpx.AsyncClient(
        base_url="http://robot",
        transport=httpx.MockTransport(handler),
        headers={"Opentrons-Version": "2"},
    )
    assert asyncio.run(robot.status())["connected"]
    assert asyncio.run(robot.capture())[1] == (64, 48)
    assert set(calls) == {
        ("GET", path)
        for path in (
            "/health",
            "/pipettes",
            "/modules",
            "/calibration/status",
            "/camera",
        )
    } | {("POST", "/camera/picture")}


@pytest.mark.parametrize(
    "content, content_type", [(b"not a jpeg", "image/jpeg"), (b"{}", "application/json")]
)
def test_invalid_camera_response_is_not_saved(content, content_type):
    robot = Robot("http://robot")
    robot.client = lambda timeout=5: httpx.AsyncClient(
        base_url="http://robot",
        transport=httpx.MockTransport(
            lambda request: httpx.Response(
                200,
                content=content,
                headers={"Content-Type": content_type},
            )
        ),
    )
    with pytest.raises(CameraError, match="invalid_image"):
        asyncio.run(robot.capture())


def test_api_contract_contains_no_passwords(console):
    client, _, _ = console
    login(client)
    result = client.get("/api/v1/users")
    assert "password" not in json.dumps(result.json())
