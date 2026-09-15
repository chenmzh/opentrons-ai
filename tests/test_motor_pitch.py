"""Synthetic signal tests do not constitute physical motor calibration."""

import unittest

try:
    import numpy as np
except ModuleNotFoundError:
    np = None

if np is not None:
    from opentrons_ai.motor_pitch import describe_frequency, spectral_peaks


@unittest.skipIf(np is None, "Optional music analysis environment is not installed")
class MotorPitchTests(unittest.TestCase):
    def setUp(self):
        self.rate = 16000
        self.time = np.arange(self.rate) / self.rate

    def test_known_note_and_cents(self):
        result = describe_frequency(440 * 2 ** (15 / 1200))
        self.assertEqual(result["nearest_note"], "A4")
        self.assertAlmostEqual(result["cents_from_note"], 15)

    def test_sine_frequency_estimation(self):
        for frequency in (293.6648, 349.2282, 587.3295):
            with self.subTest(frequency=frequency):
                samples = 0.1 * np.sin(2 * np.pi * frequency * self.time)
                result = spectral_peaks(samples, self.rate)
                self.assertEqual(result["status"], "peaks_found")
                self.assertLess(abs(result["peaks"][0]["frequency_hz"] - frequency), 0.05)

    def test_strong_harmonic_is_reported_separately(self):
        samples = 0.1 * np.sin(2 * np.pi * 300 * self.time)
        samples += 0.3 * np.sin(2 * np.pi * 600 * self.time)
        result = spectral_peaks(samples, self.rate)
        self.assertAlmostEqual(result["peaks"][0]["frequency_hz"], 600, places=2)
        self.assertAlmostEqual(result["peaks"][1]["frequency_hz"], 300, places=2)

    def test_silence_and_clipping_are_rejected(self):
        self.assertEqual(spectral_peaks(np.zeros(self.rate), self.rate)["status"], "too_quiet")
        samples = np.sign(np.sin(2 * np.pi * 300 * self.time))
        self.assertEqual(spectral_peaks(samples, self.rate)["status"], "clipped")


if __name__ == "__main__":
    unittest.main()
