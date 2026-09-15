"""Inspect recorded motor spectral peaks; never mistake a harmonic for proven F0.

Optional dependency: numpy==2.2.6. This module does not control the robot.
"""

import argparse
import json
import math
import wave

import numpy as np

NOTE_NAMES = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")


def describe_frequency(frequency_hz):
    if not math.isfinite(frequency_hz) or frequency_hz <= 0:
        raise ValueError("Frequency must be finite and positive")
    midi = 69 + 12 * math.log2(frequency_hz / 440.0)
    nearest = round(midi)
    return {
        "frequency_hz": frequency_hz,
        "nearest_note": f"{NOTE_NAMES[nearest % 12]}{nearest // 12 - 1}",
        "cents_from_note": 100 * (midi - nearest),
    }


def spectral_peaks(samples, sample_rate_hz):
    """Return strongest in-band peaks, not an asserted perceived fundamental."""
    values = np.asarray(samples, dtype=float)
    if values.ndim != 1 or sample_rate_hz < 8000 or len(values) < sample_rate_hz / 2:
        raise ValueError("Provide at least 0.5 s of mono audio sampled at >=8 kHz")
    if not np.isfinite(values).all():
        raise ValueError("Nonfinite audio samples")
    clipped_fraction = float(np.mean(np.abs(values) >= 0.999))
    values = values - np.mean(values)
    rms = float(np.sqrt(np.mean(values**2)))
    result = {
        "rms_dbfs": 20 * math.log10(max(rms, 1e-15)),
        "clipped_fraction": clipped_fraction,
        "peaks": [],
        "interpretation": "Spectral components; fundamental pitch is not established.",
    }
    if rms < 1e-5 or clipped_fraction > 0.01:
        result["status"] = "too_quiet" if rms < 1e-5 else "clipped"
        return result
    n = len(values)
    magnitude = np.abs(np.fft.rfft(values * np.hanning(n)))
    frequencies = np.fft.rfftfreq(n, 1 / sample_rate_hz)
    candidates = (
        np.flatnonzero((magnitude[1:-1] > magnitude[:-2]) & (magnitude[1:-1] >= magnitude[2:])) + 1
    )
    candidates = candidates[(frequencies[candidates] >= 60) & (frequencies[candidates] <= 3000)]
    if not len(candidates):
        result["status"] = "no_peaks"
        return result
    strongest = float(max(magnitude[candidates]))
    noise_floor = float(np.median(magnitude[(frequencies >= 60) & (frequencies <= 3000)]))
    for index in sorted(candidates, key=lambda i: magnitude[i], reverse=True):
        if magnitude[index] < strongest / 10 or magnitude[index] < noise_floor * 10:
            continue
        left, middle, right = np.log(np.maximum(magnitude[index - 1 : index + 2], 1e-30))
        denominator = left - 2 * middle + right
        fraction = 0.5 * (left - right) / denominator if denominator else 0.0
        frequency_hz = float((index + np.clip(fraction, -0.5, 0.5)) * sample_rate_hz / n)
        if any(abs(p["frequency_hz"] - frequency_hz) < 5 for p in result["peaks"]):
            continue
        peak = describe_frequency(frequency_hz)
        peak["relative_db"] = float(20 * np.log10(magnitude[index] / strongest))
        result["peaks"].append(peak)
        if len(result["peaks"]) == 5:
            break
    result["status"] = "peaks_found" if result["peaks"] else "no_tonal_peaks"
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("wav_path")
    parser.add_argument("--start-s", type=float, default=0)
    parser.add_argument("--duration-s", type=float, default=1)
    args = parser.parse_args()
    if not math.isfinite(args.start_s) or args.start_s < 0:
        parser.error("start-s must be finite and nonnegative")
    if not math.isfinite(args.duration_s) or not 0.5 <= args.duration_s <= 30:
        parser.error("duration-s must be between 0.5 and 30")
    with wave.open(args.wav_path, "rb") as recording:
        if recording.getsampwidth() != 2 or recording.getnchannels() != 1:
            parser.error("Use a mono 16-bit PCM WAV recording")
        rate = recording.getframerate()
        recording.setpos(int(args.start_s * rate))
        raw = recording.readframes(int(args.duration_s * rate))
    samples = np.frombuffer(raw, dtype="<i2").astype(float) / 32768.0
    print(json.dumps(spectral_peaks(samples, rate), indent=2))


if __name__ == "__main__":
    main()
