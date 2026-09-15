"""Clock-aligned descriptive analysis; strongest peaks are not asserted F0."""

import datetime
import json
import re
import sys
import wave
from pathlib import Path

import numpy as np

out = Path(sys.argv[1] if len(sys.argv) > 1 else "runs/music/limits-20260914")
timing = json.loads((out / "timing.json").read_text())
clock = min(timing["clock_before"] + timing["clock_after"], key=lambda v: v["rtt_s"])


def stamp(t):
    return datetime.datetime.fromisoformat(t.replace("Z", "+00:00")).timestamp()


def when(c, k):
    return stamp(c[k]) + clock["host_minus_robot_s"] - timing["audio_start_host_estimate"]


commands = json.loads((out / "commands.json").read_text())["data"]
with wave.open(str(out / "recording.wav")) as w:
    rate = w.getframerate()
    audio = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").astype(float) / 32768
blocks = []
current = None
for c in commands:
    if c["commandType"] == "comment":
        text = c["params"]["message"]
        if text.startswith("BLOCK_BEGIN"):
            m = re.search(r"index=(\d+) kind=(\w+) value=([\d.]+)", text)
            current = dict(
                index=int(m[1]),
                kind=m[2],
                value=float(m[3]),
                start_s=when(c, "completedAt"),
                moves=[],
            )
        if text.startswith("BLOCK_END"):
            current["end_s"] = when(c, "startedAt")
            blocks.append(current)
            current = None
    elif current and c["commandType"] == "moveToCoordinates":
        current["moves"].append(
            dict(start_s=when(c, "startedAt"), end_s=when(c, "completedAt"), params=c["params"])
        )


def peaks(values, lower=20, upper=6000, count=12):
    values = values - values.mean()
    n = len(values)
    mag = np.abs(np.fft.rfft(values * np.hanning(n)))
    freq = np.fft.rfftfreq(n, 1 / rate)
    ix = np.flatnonzero((mag[1:-1] > mag[:-2]) & (mag[1:-1] >= mag[2:])) + 1
    ix = ix[(freq[ix] >= lower) & (freq[ix] <= upper)]
    selected = []
    for i in sorted(ix, key=lambda j: mag[j], reverse=True):
        log = np.log(np.maximum(mag[i - 1 : i + 2], 1e-20))
        denom = log[0] - 2 * log[1] + log[2]
        delta = 0.5 * (log[0] - log[2]) / denom if denom else 0
        hz = float((i + np.clip(delta, -0.5, 0.5)) * rate / n)
        if any(abs(hz - p["hz"]) < max(3, 2 * rate / n) for p in selected):
            continue
        selected.append(dict(hz=hz, db=float(20 * np.log10(max(mag[i] / n, 1e-20)))))
        if len(selected) == count:
            break
    return selected


for block in blocks:
    if block["kind"] == "RANGE":
        summaries = []
        for move in block["moves"]:
            t0, t1 = move["start_s"], move["end_s"]
            # Central window; use small windows at high speeds to avoid ramps.
            window = 0.6 if block["value"] <= 32 else (0.16 if block["value"] <= 128 else 0.06)
            mid = (t0 + t1) / 2
            values = audio[round((mid - window / 2) * rate) : round((mid + window / 2) * rate)]
            selected = peaks(values)
            summaries.append(
                dict(
                    duration_s=t1 - t0,
                    midpoint_s=mid,
                    window_s=window,
                    rms_dbfs=float(20 * np.log10(max(np.std(values), 1e-20))),
                    peaks=selected,
                    clipped_fraction=float(np.mean(np.abs(values) >= 0.999)),
                )
            )
        block["spectra"] = summaries
        print(
            "RANGE",
            block["value"],
            "dur",
            round(np.median([m["duration_s"] for m in summaries]), 3),
            "rms",
            round(np.median([m["rms_dbfs"] for m in summaries]), 1),
            "peaks",
            [[round(p["hz"], 1) for p in m["peaks"][:5]] for m in summaries],
        )
    else:
        starts = np.array([m["start_s"] for m in block["moves"]])
        intervals = np.diff(starts)
        total = block["end_s"] - block["start_s"]
        block["timing"] = dict(
            median_onset_interval_s=float(np.median(intervals)),
            mean_onset_interval_s=float(np.mean(intervals)),
            interval_cv=float(np.std(intervals) / np.mean(intervals)),
            actual_block_s=total,
            notes_per_s=16 / total,
            median_move_s=float(np.median([m["end_s"] - m["start_s"] for m in block["moves"]])),
            achieved_sixteenth_bpm=15 / float(np.median(intervals)),
        )
        print("RHYTHM", block["value"], block["timing"])
(out / "descriptive-analysis.json").write_text(
    json.dumps(dict(rate_hz=rate, clock=clock, blocks=blocks), indent=2)
)
