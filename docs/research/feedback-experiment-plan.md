# Prospective acoustic-feedback validation plan

Prepared on 15 September 2026 before the supplementary recordings. This is a
locally frozen analysis plan, not a registry preregistration. It supplements the
retrospective human–AI case study and does not benchmark autonomous LLMs.

## Question and conditions

Can acoustic feedback recover from a deliberately mis-scaled speed–frequency
mapping and transfer to notes excluded from the calibration recording?

- Hardware: the previously confirmed OT-2 configuration, no tips or liquid
  handling, unchanged drive settings, fixed Y and post-home Z.
- Working interval: X 146.5–246.5 mm with at least 5 mm inset; measurement
  strokes use X 161.5–231.5 mm. Approach speed 30 mm/s; measurement cap 110 mm/s.
- Initial mapping: 1.08 times the earlier 4.98375 Hz/(mm/s) factor. The 8% scale
  error is intentionally injected in software. It is not observed hardware drift.
- Calibration: C4, E4, G4, each twice in each direction, 12 strokes, randomized
  order with seed 20260915. Each stroke is preceded by positioning and quiet.
- Fit: estimate pitch without target-note input, retain measurements meeting
  the frozen harmonic-consistency criterion, and calculate the median of
  measured Hz / commanded mm/s. At least two accepted observations per note
  and both directions must be represented; otherwise stop and report failure.
- Test: D4, F4, A4, excluded from the calibration recording. Each note is tested
  twice in each direction under both the initial and fitted mapping: 24 strokes
  in a separate recording, randomized with seed 20260916. Test results cannot
  change the fit or scoring algorithm.

## Measurement and stopping

Record 48 kHz mono 16-bit audio through the default headset microphone. Preserve
clock alignment samples and command timing locally. Use a central 0.4 s window
within each stroke, with at least 0.2 s excluded at either end where duration
permits. Align using measured host/robot clock offsets; do not tune alignment to
test-note labels. Report the alignment uncertainty inherited from host recording
start estimation. Microphone geometry is not quantified.

The target-independent estimator searches candidate fundamentals in 180–650 Hz.
It scores spectral peaks near the first six harmonics after local spectral
background normalization, requires at least three qualifying harmonics,
including an odd harmonic, and reports unsupported or competing octave
interpretations as uncertain. Exact implementation and synthetic checks are
saved before recording. Target frequencies are used only after estimation to
calculate error in cents. This bounded search assumes the selected register and
is not a general-purpose audio transcription method.

Primary endpoint: proportion of all scheduled held-out strokes with an accepted
estimate within 25 cents of the target. Uncertain/missing estimates count as
failures in that denominator. Also report median absolute cents error among
accepted estimates, uncertain counts, direction-specific results, and descriptive
paired differences. No independence-based significance claim is planned.

Execute one calibration recording and one held-out recording, with no repeat to
select favorable outcomes. Stop on command validation failure, unavailable robot,
recording failure, inadequate fit evidence, or ambiguous execution state. Any
method revision after observing real recordings must be documented and assessed
in a fresh recording, rather than silently applied to the frozen test.

## Role attribution and limits

The human requested additional experiments and retained the operating scope.
The agent designed this test and will inspect the calibration result before
authorizing a fitted test artifact. Numerical tools estimate and fit frequencies.
The test evaluates acoustic feedback versus a frozen perturbed mapping. It does
not isolate AI from ordinary numerical calibration: the agent knows the earlier
mapping, and the fitted update is a conventional estimator. No claim of reduced
human effort, sample efficiency, novel control law, or model superiority follows.
