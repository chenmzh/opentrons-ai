"""Unconfigured deployments must not contact a default physical robot."""

import asyncio
from pathlib import Path
from unittest.mock import Mock

import pytest

from opentrons_ai.music_runner import RobotAPI, check_hardware
from opentrons_ai.robot import CameraError, Robot


def test_music_without_endpoint_makes_no_request(monkeypatch, tmp_path):
    monkeypatch.delenv("OT2_URL", raising=False)
    api = RobotAPI(tmp_path)
    api.opener = Mock()
    with pytest.raises(RuntimeError, match="OT2_URL"):
        api.request("/health")
    api.opener.open.assert_not_called()
    assert not list(tmp_path.iterdir())


def test_music_requires_explicit_identity_before_health_request(monkeypatch):
    monkeypatch.delenv("OT2_EXPECTED_NAME", raising=False)
    api = Mock()
    with pytest.raises(RuntimeError, match="OT2_EXPECTED_NAME"):
        check_hardware(api)
    api.request.assert_not_called()


def test_configured_identity_mismatch_stops_after_health(monkeypatch):
    monkeypatch.setenv("OT2_EXPECTED_NAME", "test-calibrated-robot")
    api = Mock()
    api.request.return_value = {"name": "different-test-robot", "api_version": "26.6.0"}
    with pytest.raises(RuntimeError, match="身份"):
        check_hardware(api)
    api.request.assert_called_once_with("/health")


def test_music_reads_endpoint_from_environment(monkeypatch):
    monkeypatch.setenv("OT2_URL", "http://robot.invalid:31950/")
    assert RobotAPI(Path("unused")).url == "http://robot.invalid:31950"


def test_unconfigured_dashboard_is_disconnected_without_network():
    robot = Robot("")
    robot.client = Mock(side_effect=AssertionError("Must not contact network"))
    status = asyncio.run(robot.status())
    assert status["connected"] is False
    assert status["address"] is None
    with pytest.raises(CameraError) as error:
        asyncio.run(robot.capture())
    assert error.value.code == "robot_unreachable"
    robot.client.assert_not_called()
