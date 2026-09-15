# Supplementary acoustic-feedback validation

Experiment date: 15 September 2026, following the original measurements on
14 September. Author: Mingzhe Chen. This is an exploratory same-device follow-up,
not an independent LLM benchmark. No additional robot execution is triggered by
reading this document or rebuilding the manuscript.

## Outcome

With an intentionally injected 8% error in the speed–frequency coefficient,
numerical feedback improved the frozen held-out endpoint from **0/12 to 8/12**
strokes with an accepted estimate within ±25 cents. The feedback condition had
**four uncertain estimates**, which remain failures in the denominator.

| Condition | Scheduled strokes | Accepted | Uncertain | Within ±25 cents | Median absolute cents, accepted only |
|---|---:|---:|---:|---:|---:|
| Fixed perturbed mapping | 12 | 4 | 8 | 0 | 1066.83 |
| Fitted mapping | 12 | 8 | 4 | 8 | 0.37 |

The 0.37-cent statistic covers only eight accepted estimates. It does not
establish sub-cent performance for all notes or perceptual accuracy. Fixed-arm
accepted estimates selected octave-shifted candidates, so its 1066.83-cent
median is not the injected error magnitude (approximately −133.2 cents).

For fitted playback, D4 passed 1/4, F4 passed 4/4, and A4 passed 3/4. Each direction
passed 4/6. Two uncertain estimates had competing candidates, and two had
insufficient harmonics. Accepted fitted errors ranged from −8.13 to +0.31 cents.
No uncertain or failed trial was deleted, manually octave-corrected, or rerun
to improve the reported result.

## Frozen design and feedback decision

The [plan](feedback-experiment-plan.md), estimator, and runner were copied and
hashed before recording. Synthetic detector checks and offline trajectory tests
passed beforehand. The plan was frozen locally, not registered externally.

1. Use `k_initial = 5.38245 Hz/(mm/s)`, an 8% increase from the prior coefficient.
2. Record C4, E4, and G4, each twice in each direction: 12 calibration strokes.
3. Estimate pitch from central 0.4 s waveform windows without target-note or
   speed inputs to the detector. It searches a declared 180–650 Hz register.
4. Take the prescribed median of accepted measured-frequency/speed ratios.
5. Freeze the resulting coefficient and test D4, F4, A4 in a separate recording,
   interleaving both conditions in a balanced randomized order.

Calibration accepted 11/12 candidates, with one uncertain result. Four accepted
candidates were octave-shifted relative to the expected injected-error relation.
The median remained `4.98346880007365 Hz/(mm/s)`. The agent reviewed the evidence,
recorded the ambiguity, and proceeded using this exact fit without substituting
the known historical coefficient. The scoring source and thresholds were
unchanged for the held-out data. The human authorized supplementation and did
not provide a trial-specific numerical correction during this follow-up.

The feedback update is conventional numerical estimation. The comparison tests
feedback recovery relative to a deliberately perturbed fixed mapping. The agent
designed and orchestrated the procedure and reviewed the update, but these data
do not isolate its incremental benefit over an ordinary automated fitter.

## Execution and geometry

| Recording | Successful commands | All movements, including positioning | Measurement strokes |
|---|---:|---:|---:|
| Calibration | 77 | 24 | 12 |
| Held-out comparison | 149 | 48 | 24 |

Both final states were `succeeded` without recorded errors. Robot-side simulation
and exact command validation preceded each run. The robot was checked idle and
matched the configured installation. All 72 post-home movements retained
Y=178.75 mm and Z=189.27 mm; X endpoints were 161.5–231.5 mm, within the chosen
100 mm interval and 5 mm inset. Actual speed did not exceed 88.292 mm/s, below
the supplementary validator's 110 mm/s cap. No tips or liquid handling were
involved, and no drive setting was changed.

The headset input was available at the previously configured volume of 0.20.
Recordings used 48 kHz mono 16-bit PCM. Microphone position and sampling-clock
accuracy were not independently calibrated. Timing used recorded clock-offset
samples with an estimated ±0.15 s audio alignment uncertainty; no target-based
alignment was fitted. Uncertainty and missing harmonics limit the result.

## Reproduce the artifacts

The reviewed [numerical evidence](data/feedback-evidence.json) retains all 36
measurement rows, condition summaries, source hashes, frozen-source hashes,
execution counts, and the agent's concise fit decision. It contains no raw
device identity, network configuration, or execution identifiers. Original audio
and detailed transport logs remain local; full independent acoustic reanalysis
therefore still requires access to the original recordings.

With the research dependencies installed, these commands **only prepare local
protocol artifacts**:

```bash
PYTHONPATH=src .venv-research/bin/python -m opentrons_ai.research.feedback_experiment \
  calibration runs/music/feedback-calibration-new
PYTHONPATH=src .venv-research/bin/python -m opentrons_ai.research.feedback_experiment \
  test runs/music/feedback-test-new --fitted-k 4.98346880007365
```

The directories must not already exist. Hardware execution additionally requires
local robot configuration, current physical setup, a working microphone, and
`--execute`. It checks state and simulation before motion. Do not reuse the
historical fitted coefficient as evidence of current calibration. The `analyze`
subcommand operates on an existing local recording directory without contacting
the robot. The recorded original sources, including the frozen estimator, are
kept with each local recording; do not silently change them when reanalyzing.

## 中文结果说明

本次补测在同一设备的次日完成：先校准 12 次发声，再独立录音比较 24 次发声。
人为注入的 8% 映射偏差经数值反馈更新后，预设 ±25 音分指标从 0/12 改善到
8/12，仍有 4/12 不确定。检测器未读取目标音符，未在测试后修改评分或补跑挑选
结果。两次运行均成功，固定归零后的 Z；共有 72 次含定位的移动。
这支持特定条件下声学反馈的作用，不证明 AI 优于常规自动校准，也不证明全音域
或人耳听感达到亚音分精度。人的作用是提出并授权补测，智能体设计、实现和检查
流程，数值工具完成拟合与独立评分。
