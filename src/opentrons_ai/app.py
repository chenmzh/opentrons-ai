"""Authenticated foundation API: inventory, observation, and optional pictures."""

import asyncio
import hashlib
import json
import math
import os
import secrets
import sqlite3
import time
from pathlib import Path
from typing import Literal
from uuid import uuid4

from argon2 import PasswordHasher
from argon2.exceptions import VerificationError
from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field, field_validator

from .robot import CameraError, Robot
from .storage import Store, utc_now

ROOT = Path(__file__).resolve().parents[2]
PASSWORDS = PasswordHasher()
DUMMY_HASH = PASSWORDS.hash(secrets.token_urlsafe(20))


class Login(BaseModel):
    username: str = Field(min_length=1, max_length=64, pattern=r"^[a-zA-Z0-9_.-]+$")
    password: str = Field(min_length=1, max_length=256)


class UserCreate(Login):
    password: str = Field(min_length=12, max_length=256)
    role: Literal["admin", "operator", "viewer"]


class HardwareInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    name: str = Field(min_length=1, max_length=120)
    category: Literal["pipette", "labware", "tiprack", "module", "other"]
    model: str = Field(default="", max_length=120)
    serial: str = Field(default="", max_length=120)
    notes: str = Field(default="", max_length=1000)
    definition: dict | None = None

    @field_validator("definition")
    @classmethod
    def check_definition(cls, definition):
        if definition is None:
            return None
        try:
            if len(json.dumps(definition)) > 500_000:
                raise ValueError()
            if definition["schemaVersion"] != 2:
                raise ValueError()
            if not isinstance(definition["namespace"], str) or not definition["namespace"]:
                raise ValueError()
            if type(definition["version"]) is not int or definition["version"] < 1:
                raise ValueError()
            if not definition["parameters"]["loadName"]:
                raise ValueError()
            wells = definition["wells"]
            ordering = [well for column in definition["ordering"] for well in column]
            if not wells or len(ordering) != len(set(ordering)) or set(ordering) != set(wells):
                raise ValueError()
            for well in wells.values():
                for key in ("totalLiquidVolume", "depth"):
                    if not math.isfinite(well[key]) or well[key] <= 0:
                        raise ValueError()
                for key in ("x", "y", "z"):
                    if not math.isfinite(well[key]):
                        raise ValueError()
        except (KeyError, TypeError, ValueError):
            raise ValueError("invalid_labware_definition") from None
        return definition


class ImportInput(BaseModel):
    items: list[HardwareInput] = Field(min_length=1, max_length=200)


class Revision(BaseModel):
    revision: int = Field(ge=1)


def create_app(data_dir=None, robot=None, secure_cookie=None):
    directory = Path(data_dir or os.environ.get("OT2_DATA_DIR", ROOT / ".local"))
    store = Store(directory)
    photos = directory / "captures"
    photos.mkdir(exist_ok=True)
    robot = robot or Robot(os.environ.get("OT2_URL", ""))
    secure = (
        secure_cookie if secure_cookie is not None else os.getenv("OT2_SECURE_COOKIE", "1") == "1"
    )
    app = FastAPI(title="Opentrons AI Console", docs_url=None, redoc_url=None, openapi_url=None)
    app.state.store = store
    app.state.robot = robot
    status_cache = {"value": None, "time": 0}
    status_lock = asyncio.Lock()

    @app.middleware("http")
    async def boundaries(request, call_next):
        try:
            length = int(request.headers.get("content-length", "0") or 0)
        except ValueError:
            return JSONResponse({"detail": "invalid_input"}, status_code=400)
        if length > 2_000_000:
            return JSONResponse({"detail": "file_too_large"}, status_code=413)
        if request.method not in ("GET", "HEAD", "OPTIONS"):
            if "transfer-encoding" in request.headers:
                return JSONResponse({"detail": "invalid_input"}, status_code=400)
            if request.headers.get("x-requested-with") != "opentrons-console":
                return JSONResponse({"detail": "csrf_failed"}, status_code=403)
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "same-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; img-src 'self' blob:; style-src 'self'; "
            "script-src 'self'; connect-src 'self'; frame-ancestors 'none'"
        )
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        return response

    @app.exception_handler(RequestValidationError)
    async def invalid_request(request, exc):
        return JSONResponse({"detail": "invalid_input"}, status_code=422)

    def current_user(request: Request):
        digest = hashlib.sha256(request.cookies.get("ot2_session", "").encode()).hexdigest()
        with store.connect() as db:
            row = db.execute(
                "SELECT u.username, u.role, s.csrf FROM sessions s JOIN users u "
                "ON s.username=u.username WHERE digest=? AND expires>?",
                (digest, time.time()),
            ).fetchone()
        if not row:
            raise HTTPException(401, "unauthorized")
        user = dict(row)
        if request.method not in ("GET", "HEAD") and not secrets.compare_digest(
            request.headers.get("x-csrf-token", ""), user["csrf"]
        ):
            raise HTTPException(403, "csrf_failed")
        return user

    def admin(user=Depends(current_user)):
        if user["role"] != "admin":
            raise HTTPException(403, "forbidden")
        return user

    def operator(user=Depends(current_user)):
        if user["role"] not in ("admin", "operator"):
            raise HTTPException(403, "forbidden")
        return user

    @app.post("/api/v1/login")
    def login(payload: Login, request: Request, response: Response):
        ip = request.client.host if request.client else "unknown"
        now = time.time()
        with store.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute("DELETE FROM attempts WHERE timestamp<?", (now - 300,))
            count = db.execute("SELECT COUNT(*) FROM attempts WHERE ip=?", (ip,)).fetchone()[0]
            if count >= 10:
                raise HTTPException(429, "login_limited")
            db.execute("INSERT INTO attempts VALUES (?, ?)", (ip, now))
            row = db.execute("SELECT * FROM users WHERE username=?", (payload.username,)).fetchone()
        try:
            PASSWORDS.verify(row["password_hash"] if row else DUMMY_HASH, payload.password)
        except VerificationError:
            raise HTTPException(401, "login_failed") from None
        if not row:
            raise HTTPException(401, "login_failed")
        token, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(24)
        with store.connect() as db:
            db.execute("DELETE FROM sessions WHERE expires<=?", (now,))
            db.execute("DELETE FROM attempts WHERE ip=?", (ip,))
            db.execute(
                "INSERT INTO sessions VALUES (?, ?, ?, ?)",
                (
                    hashlib.sha256(token.encode()).hexdigest(),
                    row["username"],
                    csrf,
                    now + 28800,
                ),
            )
            store.audit(db, row["username"], "login")
        response.set_cookie(
            "ot2_session", token, httponly=True, secure=secure, samesite="strict", max_age=28800
        )
        return {"username": row["username"], "role": row["role"], "csrf": csrf}

    @app.get("/api/v1/me")
    def me(user=Depends(current_user)):
        return user

    @app.post("/api/v1/logout")
    def logout(request: Request, response: Response, user=Depends(current_user)):
        with store.connect() as db:
            db.execute(
                "DELETE FROM sessions WHERE digest=?",
                (hashlib.sha256(request.cookies["ot2_session"].encode()).hexdigest(),),
            )
        response.delete_cookie("ot2_session", secure=secure, httponly=True, samesite="strict")
        return {"ok": True}

    @app.get("/api/v1/users")
    def users(user=Depends(admin)):
        with store.connect() as db:
            return [
                dict(row)
                for row in db.execute(
                    "SELECT username, role, created_at FROM users ORDER BY created_at"
                )
            ]

    @app.post("/api/v1/users", status_code=201)
    def add_user(payload: UserCreate, user=Depends(admin)):
        try:
            with store.connect() as db:
                db.execute(
                    "INSERT INTO users VALUES (?, ?, ?, ?)",
                    (
                        payload.username,
                        PASSWORDS.hash(payload.password),
                        payload.role,
                        utc_now(),
                    ),
                )
                store.audit(db, user["username"], "user_created", payload.username)
        except sqlite3.IntegrityError:
            raise HTTPException(409, "user_exists") from None
        return {"username": payload.username, "role": payload.role}

    @app.get("/api/v1/robot")
    async def robot_status(user=Depends(current_user)):
        async with status_lock:
            if status_cache["value"] is None or time.monotonic() - status_cache["time"] > 5:
                status_cache["value"] = await robot.status()
                status_cache["time"] = time.monotonic()
        return status_cache["value"]

    @app.get("/api/v1/hardware")
    def hardware(user=Depends(current_user)):
        return store.hardware()

    def insert_hardware(db, item, username):
        identifier = str(uuid4())
        db.execute(
            "INSERT INTO hardware VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                identifier,
                item.name,
                item.category,
                item.model,
                item.serial,
                item.notes,
                json.dumps(item.definition) if item.definition else None,
                "pending",
                1,
                utc_now(),
                None,
            ),
        )
        store.audit(db, username, "hardware_created", identifier)
        return identifier

    @app.post("/api/v1/hardware", status_code=201)
    def add_hardware(item: HardwareInput, user=Depends(admin)):
        with store.connect() as db:
            identifier = insert_hardware(db, item, user["username"])
        return {"id": identifier}

    @app.post("/api/v1/hardware/import", status_code=201)
    def import_hardware(payload: ImportInput, user=Depends(admin)):
        with store.connect() as db:
            ids = [insert_hardware(db, item, user["username"]) for item in payload.items]
        return {"ids": ids}

    @app.post("/api/v1/hardware/discover")
    async def discover(user=Depends(admin)):
        status = await robot.status()
        if not status.get("connected") or status.get("pipettes") is None:
            raise HTTPException(503, "robot_unreachable")
        ids = []
        with store.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            for mount, pipette in status["pipettes"].items():
                if not pipette or not pipette.get("id"):
                    continue
                if db.execute(
                    "SELECT id FROM hardware WHERE serial=?", (pipette["id"],)
                ).fetchone():
                    continue
                item = HardwareInput(
                    name=pipette["name"],
                    category="pipette",
                    model=pipette["model"],
                    serial=pipette["id"],
                    notes=f"{mount}; discovered {utc_now()}",
                )
                ids.append(insert_hardware(db, item, user["username"]))
        return {"ids": ids}

    @app.post("/api/v1/hardware/{identifier}/approve")
    def approve(identifier: str, payload: Revision, user=Depends(admin)):
        with store.connect() as db:
            updated = db.execute(
                "UPDATE hardware SET status='approved', approved_by=?, revision=revision+1 "
                "WHERE id=? AND revision=? AND status='pending'",
                (user["username"], identifier, payload.revision),
            )
            if not updated.rowcount:
                raise HTTPException(409, "revision_conflict")
            store.audit(db, user["username"], "hardware_approved", identifier)
        return {"ok": True}

    @app.get("/api/v1/captures")
    def captures(user=Depends(current_user)):
        with store.connect() as db:
            return [
                dict(row)
                for row in db.execute("SELECT * FROM captures ORDER BY created_at DESC LIMIT 100")
            ]

    @app.post("/api/v1/captures", status_code=201)
    async def capture(user=Depends(operator)):
        try:
            data, (width, height) = await robot.capture()
        except CameraError as exc:
            with store.connect() as db:
                store.audit(db, user["username"], "capture_failed", exc.code)
            raise HTTPException(503, exc.code) from None
        identifier = str(uuid4())
        path = photos / f"{identifier}.jpg"
        with path.open("xb") as output:
            output.write(data)
        path.chmod(0o600)
        created_at = utc_now()
        with store.connect() as db:
            db.execute(
                "INSERT INTO captures VALUES (?, ?, ?, ?, ?, ?)",
                (
                    identifier,
                    created_at,
                    user["username"],
                    width,
                    height,
                    hashlib.sha256(data).hexdigest(),
                ),
            )
            store.audit(db, user["username"], "capture_saved", identifier)
        return {"id": identifier, "created_at": created_at, "width": width, "height": height}

    @app.get("/api/v1/captures/{identifier}/image")
    def image(identifier: str, user=Depends(current_user)):
        with store.connect() as db:
            row = db.execute("SELECT id FROM captures WHERE id=?", (identifier,)).fetchone()
        if not row or not (photos / f"{identifier}.jpg").is_file():
            raise HTTPException(404, "not_found")
        return FileResponse(photos / f"{identifier}.jpg", media_type="image/jpeg")

    @app.get("/api/v1/audit")
    def audit(user=Depends(admin)):
        with store.connect() as db:
            return [
                dict(row) for row in db.execute("SELECT * FROM audit ORDER BY id DESC LIMIT 100")
            ]

    frontend = ROOT / "frontend" / "dist"
    if frontend.is_dir():
        app.mount("/", StaticFiles(directory=frontend, html=True), name="frontend")
    return app
