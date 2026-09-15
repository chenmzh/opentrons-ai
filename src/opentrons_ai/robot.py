"""Fixed OT-2 requests; never expose a general robot HTTP proxy."""

import asyncio
import io
from datetime import datetime, timezone

import httpx
from PIL import Image


class CameraError(Exception):
    def __init__(self, code):
        self.code = code


class Robot:
    def __init__(self, url: str):
        self.url = url.rstrip("/")
        self._capture_lock = asyncio.Lock()

    def client(self, timeout=5):
        return httpx.AsyncClient(
            base_url=self.url,
            trust_env=False,
            timeout=timeout,
            headers={"Opentrons-Version": "2"},
            follow_redirects=False,
        )

    async def status(self):
        if not self.url:
            return dict.fromkeys(["health", "pipettes", "modules", "calibration", "camera"]) | {
                "connected": False,
                "checked_at": datetime.now(timezone.utc).isoformat(),
                "address": None,
            }
        async with self.client() as client:

            async def get(path):
                try:
                    response = await client.get(path)
                    response.raise_for_status()
                    return response.json()
                except (httpx.HTTPError, ValueError):
                    return None

            paths = ["/health", "/pipettes", "/modules", "/calibration/status", "/camera"]
            values = await asyncio.gather(*(get(path) for path in paths))
        return dict(
            zip(["health", "pipettes", "modules", "calibration", "camera"], values, strict=True)
        ) | {
            "connected": values[0] is not None,
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "address": self.url,
        }

    async def capture(self):
        if not self.url:
            raise CameraError("robot_unreachable")
        if self._capture_lock.locked():
            raise CameraError("camera_busy")
        async with self._capture_lock:
            try:
                async with self.client(timeout=45) as client:
                    async with client.stream("POST", "/camera/picture") as response:
                        if response.status_code == 422:
                            raise CameraError("camera_disabled")
                        if response.status_code != 200:
                            raise CameraError("camera_failed")
                        if response.headers.get("content-type", "").split(";")[0] not in (
                            "image/jpg",
                            "image/jpeg",
                        ):
                            raise CameraError("invalid_image")
                        data = bytearray()
                        async for chunk in response.aiter_bytes():
                            data.extend(chunk)
                            if len(data) > 10 * 1024 * 1024:
                                raise CameraError("invalid_image")
                with Image.open(io.BytesIO(data)) as photo:
                    if photo.format != "JPEG" or photo.width * photo.height > 20_000_000:
                        raise CameraError("invalid_image")
                    size = photo.size
                    photo.verify()
                return bytes(data), size
            except httpx.HTTPError as exc:
                raise CameraError("robot_unreachable") from exc
            except (ValueError, OSError, Image.DecompressionBombError) as exc:
                raise CameraError("invalid_image") from exc
