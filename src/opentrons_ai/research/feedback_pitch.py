"""Target-independent, bounded-register harmonic estimator for the follow-up."""

import numpy as np


def estimate_pitch(samples, rate):
    samples = np.asarray(samples, dtype=float)
    if len(samples) < rate * 0.35:
        return {"status": "uncertain", "reason": "short_window"}
    samples = samples - samples.mean()
    nfft = 2 ** int(np.ceil(np.log2(len(samples) * 4)))
    spectrum = np.abs(np.fft.rfft(samples * np.hanning(len(samples)), n=nfft))
    hz = np.fft.rfftfreq(nfft, 1 / rate)
    peaks = np.flatnonzero((spectrum[1:-1] > spectrum[:-2]) & (spectrum[1:-1] >= spectrum[2:])) + 1
    peaks = peaks[(hz[peaks] >= 175) & (hz[peaks] <= 3950)]
    measured = []
    for index in peaks:
        if spectrum[index] < spectrum.max() * 10 ** (-35 / 20):
            continue
        frequency = hz[index]
        local = spectrum[
            (hz > frequency - 70) & (hz < frequency + 70) & (np.abs(hz - frequency) > 12)
        ]
        prominence = 20 * np.log10((spectrum[index] + 1e-15) / (np.median(local) + 1e-15))
        if prominence < 12:
            continue
        a, b, c = np.log(spectrum[index - 1 : index + 2] + 1e-15)
        correction = np.clip(0.5 * (a - c) / (a - 2 * b + c), -0.5, 0.5)
        measured.append(((index + correction) * rate / nfft, prominence))
    candidates = []
    for frequency, _ in measured:
        for harmonic in range(1, 7):
            fundamental = frequency / harmonic
            if not 180 <= fundamental <= 650:
                continue
            matches = []
            for h in range(1, 7):
                eligible = [
                    (f, p) for f, p in measured if abs(1200 * np.log2(f / (h * fundamental))) <= 18
                ]
                if eligible:
                    f, p = max(eligible, key=lambda item: item[1])
                    matches.append((h, f / h, p))
            if len(matches) < 3 or not any(h % 2 for h, _, _ in matches):
                continue
            score = sum(min(p, 45) for _, _, p in matches)
            candidates.append((score, float(np.median([f for _, f, _ in matches])), matches))
    if not candidates:
        return {"status": "uncertain", "reason": "insufficient_harmonics"}
    candidates.sort(reverse=True)
    best = candidates[0]
    alternatives = [c for c in candidates[1:] if abs(1200 * np.log2(c[1] / best[1])) > 50]
    if alternatives and alternatives[0][0] >= best[0] * 0.90:
        return {
            "status": "uncertain",
            "reason": "competing_candidates",
            "candidate_hz": best[1],
            "alternative_hz": alternatives[0][1],
        }
    return {
        "status": "accepted",
        "frequency_hz": best[1],
        "score": best[0],
        "harmonics": [h for h, _, _ in best[2]],
    }
