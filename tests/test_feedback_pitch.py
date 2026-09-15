"""Check ambiguity handling without robot access or measured test recordings."""

import pytest

np = pytest.importorskip("numpy")

from opentrons_ai.research.feedback_pitch import estimate_pitch  # noqa: E402


def test_recovers_missing_fundamental_from_odd_and_even_harmonics():
    rate = 48000
    time = np.arange(int(rate * 0.4)) / rate
    signal = sum(np.sin(2 * np.pi * 277.18 * h * time) / h for h in (2, 3, 4, 5, 6))
    result = estimate_pitch(signal, rate)
    assert result["status"] == "accepted"
    assert abs(1200 * np.log2(result["frequency_hz"] / 277.18)) < 2


def test_does_not_assign_pitch_to_silence_or_a_single_line():
    rate = 48000
    time = np.arange(int(rate * 0.4)) / rate
    for signal in (np.zeros(len(time)), np.sin(2 * np.pi * 330 * time)):
        assert estimate_pitch(signal, rate)["status"] == "uncertain"
