import json
import sys
import wave
from pathlib import Path

import numpy as np

p = Path(sys.argv[1] if len(sys.argv) > 1 else "runs/music/limits-20260914")
result = json.loads((p / "descriptive-analysis.json").read_text())
blocks = [b for b in result["blocks"] if b["kind"] == "RHYTHM"]
with wave.open(str(p / "recording.wav")) as w:
    sr = w.getframerate()
    audio = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").astype(float) / 32768
n = round(0.04 * sr)
freqs = np.fft.rfftfreq(n, 1 / sr)
mask = (freqs >= 100) & (freqs <= 3000)


def psd(t):
    lo = round(t * sr) - n // 2
    x = audio[lo : lo + n]
    x = x - x.mean()
    return np.abs(np.fft.rfft(x * np.hanning(n)))[mask] ** 2 / n**2


quiet = np.median(
    [psd(t) for t in np.arange(blocks[0]["start_s"] - 1.5, blocks[0]["start_s"] - 0.4, 0.04)],
    axis=0,
)


def features(t):
    x = np.maximum(psd(t) - quiet, 0)
    x = np.sqrt(x)
    return x / max(np.linalg.norm(x), 1e-15)


labels = [38, 41, 50, 41] * 4
ref = blocks[0]
refs = []
for m in ref["moves"]:
    refs.append(
        np.mean(
            [features(t) for t in np.arange(m["start_s"] + 0.3, m["end_s"] - 0.2, 0.04)], axis=0
        )
    )
refs = np.array(refs)
refs /= np.linalg.norm(refs, axis=1)[:, None]
classes = [38, 41, 50]


def classify(t, omit=None):
    f = features(t)
    sim = refs @ f
    scores = []
    for c in classes:
        idx = [i for i, label in enumerate(labels) if label == c and i != omit]
        scores.append(max(sim[idx]))
    idx = np.argmax(scores)
    return classes[idx], max(scores), sorted(scores)[-1] - sorted(scores)[-2]


# Locate changeovers on the 0.5-second calibration block, using samples near edges.
cal = blocks[1]


def agreement(shift):
    correct = []
    for i, m in enumerate(cal["moves"]):
        for frac in [0.1, 0.3, 0.5, 0.7, 0.9]:
            t = m["start_s"] + (m["end_s"] - m["start_s"]) * frac + shift
            correct.append(classify(t)[0] == labels[i])
    return np.mean(correct)


shifts = np.arange(-0.1, 0.221, 0.005)
accs = [agreement(s) for s in shifts]
best = float(shifts[np.argmax(accs)])
print("alignment offset", best, "calibration accuracy", max(accs))
rows = []
for j, b in enumerate(blocks):
    predictions = []
    margins = []
    sims = []
    for i, m in enumerate(b["moves"]):
        t = (m["start_s"] + m["end_s"]) / 2 + best
        pred, sim, margin = classify(t, omit=i if j == 0 else None)
        predictions.append(pred)
        margins.append(margin)
        sims.append(sim)
    row = dict(
        period_s=b["value"],
        correct=sum(a == b for a, b in zip(predictions, labels, strict=True)),
        total=16,
        predictions=predictions,
        median_margin=float(np.median(margins)),
        median_similarity=float(np.median(sims)),
    )
    rows.append(row)
    print(row)
(p / "note-separability.json").write_text(
    json.dumps(
        dict(
            window_s=0.04,
            alignment_offset_s=best,
            calibration_block_s=0.5,
            reference_block_s=1.0,
            results=rows,
        ),
        indent=2,
    )
)
