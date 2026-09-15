"""Stdlib host transport for the dedicated, no-tip motor music protocol."""

import argparse
import fcntl
import hashlib
import json
import math
import os
import time
import urllib.error
import urllib.request
import uuid
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

TERMINAL = {"succeeded", "failed", "stopped"}


class RobotAPI:
    def __init__(self, directory):
        self.directory = directory
        self.url = os.environ.get("OT2_URL", "").rstrip("/")
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        self.sequence = 0
        self.run_id = None

    def request(self, path, method="GET", data=None, body=None, content_type="application/json"):
        if not self.url:
            raise RuntimeError("请先在本地设置 OT2_URL")
        self.sequence += 1
        prefix = self.directory / f"{self.sequence:04d}"
        if data is not None:
            body = json.dumps(data).encode()
        intent = dict(path=path, method=method, data=data, host_time=time.time())
        Path(f"{prefix}-intent.json").write_text(json.dumps(intent))
        request = urllib.request.Request(
            self.url + path,
            data=body,
            method=method,
            headers={"Opentrons-Version": "2", "Content-Type": content_type},
        )
        try:
            with self.opener.open(request, timeout=20) as response:
                result = json.load(response)
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode(errors="replace")
            Path(f"{prefix}-error.txt").write_text(detail)
            raise RuntimeError(f"{method} {path}: HTTP {exc.code}: {detail}") from exc
        except (OSError, ValueError) as exc:
            hint = "；请求结果不明确，不会自动重发" if method != "GET" else "；停止监控"
            raise RuntimeError(f"{method} {path} 失败{hint}: {exc}") from exc
        Path(f"{prefix}-response.json").write_text(json.dumps(result))
        return result

    def upload(self, protocol_path):
        content = protocol_path.read_bytes()
        (self.directory / "uploaded-protocol.py").write_bytes(content)
        (self.directory / "protocol-sha256.txt").write_text(hashlib.sha256(content).hexdigest())
        boundary = "ot2music" + uuid.uuid4().hex
        body = (
            (
                f'--{boundary}\r\nContent-Disposition: form-data; name="files"; '
                f'filename="{protocol_path.name}"\r\nContent-Type: text/x-python\r\n\r\n'
            ).encode()
            + content
            + f"\r\n--{boundary}--\r\n".encode()
        )
        return self.request(
            "/protocols",
            "POST",
            body=body,
            content_type=f"multipart/form-data; boundary={boundary}",
        )["data"]


@contextmanager
def controller_lock(path):
    """Prevent two copies of this launcher controlling the same robot."""
    with path.open("a") as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RuntimeError("另一个音乐启动器正在运行；请等它结束") from exc
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


def check_hardware(api):
    expected_name = os.environ.get("OT2_EXPECTED_NAME", "")
    if not expected_name:
        raise RuntimeError("请先在本地设置 OT2_EXPECTED_NAME，以核对已校准的机器人")
    health = api.request("/health")
    if health.get("name") != expected_name or health.get("api_version") != "26.6.0":
        raise RuntimeError("机器人身份或软件版本与当前校准配置不符")
    pipettes = api.request("/pipettes")
    if (
        pipettes["left"].get("name") != "p300_multi_gen2"
        or pipettes["right"].get("model") is not None
    ):
        raise RuntimeError("需要已确认的左侧 p300_multi_gen2、右侧空载配置")
    if api.request("/sessions")["data"]:
        raise RuntimeError("存在其他机器人 session，请等操作完成后重试")


def wait_idle(api, timeout_s):
    deadline = time.monotonic() + timeout_s
    while True:
        runs = api.request("/runs")["data"]
        busy = [r for r in runs if r["status"] not in TERMINAL]
        if not busy:
            return [r for r in runs if r.get("current")]
        description = ", ".join(f"{r['id']} ({r['status']})" for r in busy)
        print(f"等待当前运行结束：{description}", flush=True)
        if time.monotonic() >= deadline:
            raise RuntimeError("等待超时；没有中断或启动任何运行")
        time.sleep(min(5, max(0, deadline - time.monotonic())))


def validate_commands(commands, plan, simulated, start_x_mm=196.5, max_speed_mm_s=30.0):
    if not math.isfinite(max_speed_mm_s) or not 0 < max_speed_mm_s <= 36:
        raise RuntimeError("音乐速度上限必须在已验证的 36 mm/s 以内")
    allowed = {
        "home",
        "loadPipette",
        "savePosition",
        "comment",
        "waitForDuration",
        "moveToCoordinates",
    }
    if any(c["commandType"] not in allowed or c["status"] != "succeeded" for c in commands):
        raise RuntimeError("命令包含非音乐操作或未成功执行的命令")
    moves = [c["params"] for c in commands if c["commandType"] == "moveToCoordinates"]
    expected = [dict(x_mm=start_x_mm, speed_mm_s=30.0), *plan]
    if len(moves) != len(expected):
        raise RuntimeError("机器人分析的移动数量与本地旋律不符")
    zs = set()
    for move, event in zip(moves, expected, strict=True):
        point = move["coordinates"]
        if (
            not move.get("forceDirect")
            or not 0 < move["speed"] <= max_speed_mm_s
            or not 151.5 <= point["x"] <= 241.5
            or not math.isclose(point["x"], event["x_mm"], abs_tol=1e-6)
            or not math.isclose(move["speed"], event["speed_mm_s"], abs_tol=1e-6)
            or point["y"] != 178.75
            or not math.isfinite(point["z"])
            or point["z"] < 150
        ):
            raise RuntimeError("移动坐标、速度或高度不符合已验证的计划")
        zs.add(point["z"])
    if len(zs) != 1 or (simulated and zs != {200.0}):
        raise RuntimeError("音乐移动没有保持固定 Z")
    return moves[0]["coordinates"]["z"]


def prepare(api, protocol_path, plan, start_x_mm=196.5, max_speed_mm_s=30.0):
    uploaded = api.upload(protocol_path)
    protocol_id = uploaded["id"]
    analysis_id = uploaded["analysisSummaries"][-1]["id"]
    deadline = time.monotonic() + 180
    while True:
        analysis = api.request(f"/protocols/{protocol_id}/analyses/{analysis_id}")["data"]
        if analysis["status"] == "completed":
            break
        if time.monotonic() >= deadline:
            raise RuntimeError("模拟分析等待超时；尚未启动机器人")
        time.sleep(2)
    (api.directory / "analysis.json").write_text(json.dumps(analysis, indent=2))
    if analysis.get("result") != "ok" or analysis.get("errors"):
        raise RuntimeError(f"机器人模拟未通过：{analysis.get('errors')}")
    validate_commands(
        analysis["commands"],
        plan,
        simulated=True,
        start_x_mm=start_x_mm,
        max_speed_mm_s=max_speed_mm_s,
    )
    print(f"模拟通过：{len(plan)} 个音符，固定 Z，速度不超过 {max_speed_mm_s:g} mm/s", flush=True)
    return protocol_id


def perform(
    api, protocol_id, plan, wait_timeout_s, run_timeout_s, start_x_mm=196.5, max_speed_mm_s=30.0
):
    # Recheck after analysis. Only release a terminal run, never stop an active one.
    finished = wait_idle(api, wait_timeout_s)
    check_hardware(api)
    for run in finished:
        latest = api.request(f"/runs/{run['id']}")["data"]
        if latest["status"] not in TERMINAL:
            raise RuntimeError("运行状态已改变；不切换当前运行")
        api.request(f"/runs/{run['id']}", "PATCH", {"data": {"current": False}})
    created = api.request("/runs", "POST", {"data": {"protocolId": protocol_id}})["data"]
    api.run_id = created["id"]
    (api.directory / "run-id.txt").write_text(api.run_id)
    print(f"开始归零并演奏。Run ID: {api.run_id}\n日志：{api.directory}", flush=True)
    api.request(f"/runs/{api.run_id}/actions", "POST", {"data": {"actionType": "play"}})
    deadline = time.monotonic() + run_timeout_s
    previous = None
    last_report = 0.0
    while True:
        state = api.request(f"/runs/{api.run_id}")["data"]
        (api.directory / "run-state.json").write_text(json.dumps(state, indent=2))
        if state["status"] != previous or time.monotonic() - last_report >= 10:
            print(f"状态：{state['status']}", flush=True)
            previous, last_report = state["status"], time.monotonic()
        if state["status"] in TERMINAL:
            break
        if time.monotonic() >= deadline:
            raise RuntimeError("监控超时；机器人可能仍在运行，不会重新发送 play")
        time.sleep(2)
    if state["status"] != "succeeded" or state.get("errors"):
        raise RuntimeError(f"演奏未成功结束：{state['status']} {state.get('errors')}")
    result = api.request(f"/runs/{api.run_id}/commands?pageLength=1000")
    (api.directory / "commands.json").write_text(json.dumps(result, indent=2))
    if len(result["data"]) != result["meta"]["totalLength"]:
        raise RuntimeError("命令日志不完整，无法核对全部移动")
    z_mm = validate_commands(
        result["data"], plan, simulated=False, start_x_mm=start_x_mm, max_speed_mm_s=max_speed_mm_s
    )
    print(f"演奏成功；{len(result['data'])} 条命令成功，移动 Z={z_mm:.2f} mm。", flush=True)


def main(
    protocol_path,
    plan,
    *,
    title="Jingle Bells：主歌 + 副歌",
    slug="jingle-bells",
    start_x_mm=196.5,
    max_speed_mm_s=30.0,
):
    parser = argparse.ArgumentParser(description=f"{title}：上传、模拟、等待空闲并演奏")
    parser.add_argument("--dry-run", action="store_true", help="只检查本地音符和运动，不连接机器人")
    parser.add_argument("--simulate-only", action="store_true", help="只做机器人模拟，不启动运动")
    parser.add_argument("--wait-timeout", type=float, default=900, help="等待空闲的秒数，默认 900")
    parser.add_argument("--run-timeout", type=float, default=600, help="运行监控秒数，默认 600")
    args = parser.parse_args()
    if any(not math.isfinite(v) or v < 0 for v in (args.wait_timeout, args.run_timeout)):
        parser.error("等待时间必须是有限的非负秒数")
    print(
        f"{title}，{len(plan)} 个音符，标称音符时长 {sum(e['duration_s'] for e in plan):.2f} 秒。",
        flush=True,
    )
    if args.dry_run:
        print("本地检查通过；没有连接机器人。")
        return 0
    root = protocol_path.parent.parent / "runs" / "music"
    root.mkdir(parents=True, exist_ok=True)
    api = None
    try:
        with controller_lock(root / "controller.lock"):
            directory = root / (
                slug + "-" + datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:6]
            )
            directory.mkdir()
            (directory / "composition.json").write_text(
                json.dumps(
                    dict(
                        title=title,
                        start_x_mm=start_x_mm,
                        max_speed_mm_s=max_speed_mm_s,
                        notes=plan,
                    ),
                    indent=2,
                )
            )
            api = RobotAPI(directory)
            print(f"日志：{directory}", flush=True)
            wait_idle(api, args.wait_timeout)
            check_hardware(api)
            protocol_id = prepare(api, protocol_path, plan, start_x_mm, max_speed_mm_s)
            if not args.simulate_only:
                perform(
                    api,
                    protocol_id,
                    plan,
                    args.wait_timeout,
                    args.run_timeout,
                    start_x_mm,
                    max_speed_mm_s,
                )
        return 0
    except (RuntimeError, OSError, KeyboardInterrupt) as exc:
        print(f"已退出：{exc or '用户中断'}", flush=True)
        if api is not None:
            print(f"日志：{api.directory}", flush=True)
            if api.run_id:
                print(
                    f"Run ID: {api.run_id}；退出监控不会停止机器人，请查看其当前状态。", flush=True
                )
        return 1
