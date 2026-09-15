"""Confirm expected harmonic components against quiet audio and temporal persistence.

These target-conditioned detections do not uniquely establish perceived F0.
"""

import json
import sys
import wave
from pathlib import Path

import numpy as np

p = Path(sys.argv[1])
data = json.loads((p / "descriptive-analysis.json").read_text())
alignment = json.loads((p / "note-separability.json").read_text())["alignment_offset_s"]
with wave.open(str(p / "recording.wav")) as w:
    sr = w.getframerate()
    audio = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").astype(float) / 32768
rows = []
for block in data["blocks"]:
    if block["kind"] != "RANGE":
        continue
    f0 = block["value"] * 4.98375
    move_results = []
    for move in block["moves"]:
        matches = []
        for harmonic in (1, 2, 3, 4, 5, 6, 7, 8, 16, 32, 64):
            target = f0 * harmonic
            if not 70 <= target <= 6000:
                continue
            window = 0.24 if target < 300 else (0.12 if block["value"] < 128 else 0.04)
            n = round(sr * window)
            step = 0.01 if block["value"] >= 128 else 0.04
            fs = np.fft.rfftfreq(n, 1 / sr)
            target_mask = (fs > target * 0.94) & (fs < target * 1.06)
            local_mask = (
                (fs > max(20, target - max(200, target * 0.25)))
                & (fs < target + max(200, target * 0.25))
                & (~target_mask)
            )

            def spec(t, n=n):
                start = round(t * sr) - n // 2
                x = audio[start : start + n]
                x = x - x.mean()
                return np.abs(np.fft.rfft(x * np.hanning(n))) / n

            bg = np.median(
                [spec(t) for t in np.arange(block["start_s"] - 1.4, block["start_s"] - 0.4, 0.1)],
                axis=0,
            )
            count = 0
            best = []
            current = []
            for center in np.arange(
                move["start_s"] + alignment + window / 2,
                move["end_s"] + alignment - window / 2,
                step,
            ):
                mag = spec(center)
                ix = np.flatnonzero((mag[1:-1] > mag[:-2]) & (mag[1:-1] >= mag[2:])) + 1
                ix = ix[target_mask[ix]]
                ok = False
                if len(ix):
                    j = max(ix, key=lambda z: mag[z])
                    yy = np.log(np.maximum(mag[j - 1 : j + 2], 1e-20))
                    den = yy[0] - 2 * yy[1] + yy[2]
                    hz = (j + (0.5 * (yy[0] - yy[2]) / den if den else 0)) * sr / n
                    cents = 1200 * np.log2(hz / target)
                    bg_gain = 20 * np.log10(mag[j] / max(bg[j], 1e-12))
                    prominence = 20 * np.log10(mag[j] / max(np.median(mag[local_mask]), 1e-12))
                    ok = abs(cents) <= 25 and bg_gain >= 10 and prominence >= 8
                if ok:
                    current.append(
                        dict(hz=float(hz), center_s=float(center), bg_gain_db=float(bg_gain))
                    )
                else:
                    if len(current) > len(best):
                        best = current
                    current = []
            if len(current) > len(best):
                best = current
            span = (len(best) - 1) * step if best else 0
            if span >= max(0.04, window / 2):
                matches.append(
                    dict(
                        harmonic=harmonic,
                        component_hz=float(np.median([x["hz"] for x in best])),
                        inferred_base_hz=float(np.median([x["hz"] for x in best])) / harmonic,
                        frame_center_span_s=span,
                        window_s=window,
                        midpoint_s=float(np.mean([x["center_s"] for x in best])),
                        median_above_quiet_db=float(np.median([x["bg_gain_db"] for x in best])),
                    )
                )
        move_results.append(matches)
    row = dict(speed_mm_s=block["value"], expected_base_hz=f0, moves=move_results)
    rows.append(row)
    print(
        round(block["value"], 5),
        round(f0, 3),
        [
            [
                (x["harmonic"], round(x["component_hz"], 1), round(x["frame_center_span_s"], 2))
                for x in m
            ]
            for m in move_results
        ],
    )
(p / "harmonic-tracking.json").write_text(json.dumps(rows, indent=2))
