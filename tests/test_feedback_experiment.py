"""Offline checks of the supplementary experiment's frozen motion plan."""

import copy

import pytest

pytest.importorskip("numpy")

from opentrons_ai.research.feedback_experiment import compose, validate


def commands(trials):
    return [
        {"commandType": "moveToCoordinates", "status": "succeeded",
         "params": {"forceDirect": True, "speed": speed,
                    "coordinates": {"x": x, "y": 178.75, "z": 200.0}}}
        for trial in trials
        for x, speed in ((trial["start_x_mm"], 30.0),
                         (trial["end_x_mm"], trial["speed_mm_s"]))
    ]


def test_holdout_notes_and_direction_counts_are_balanced():
    calibration = compose("calibration")
    heldout = compose("test", 4.98)
    assert len(calibration) == 12 and len(heldout) == 24
    assert {t["midi"] for t in calibration}.isdisjoint(t["midi"] for t in heldout)
    for arm in ("initial", "feedback"):
        for midi in (62, 65, 69):
            for direction in (-1, 1):
                assert sum(t["arm"] == arm and t["midi"] == midi and
                           t["direction"] == direction for t in heldout) == 2


def test_validator_rejects_changed_speed_z_and_extra_movement():
    plan = compose("test", 4.98)
    original = commands(plan)
    assert validate(original, plan, True) == 200
    for change in ("speed", "z", "extra"):
        altered = copy.deepcopy(original)
        if change == "speed":
            altered[1]["params"]["speed"] = 111
        elif change == "z":
            altered[1]["params"]["coordinates"]["z"] = 199
        else:
            altered.append(copy.deepcopy(altered[-1]))
        with pytest.raises(ValueError):
            validate(altered, plan, True)
