# Pitch Range and Temporal Resolution of OT-2 Motor Music under Bounded Travel and Default Motion Settings

Study type: exploratory engineering experiment on a single device. Experiment date: 14 September 2026, using the control computer's date. Version: 1.1. Project: Opentrons AI. This project research report has not undergone peer review.

## Abstract

**Objective:** To characterize the pitch range and short-note separability of motor-generated sound from an Opentrons OT-2 without changing its default motion settings, while distinguishing command throughput from musical usability. **Methods:** Two experiments were performed on one OT-2 without tips or liquid handling. Commanded speed was capped at 400 mm/s, X travel was restricted to a 100 mm interval, and Y and Z remained fixed after homing. The experiments comprised 27 speed blocks and 12 rhythm blocks, with 311 direct movements. Analysis combined 48 kHz microphone recordings, robot command timestamps, and slow reference phrases. Target-conditioned harmonic detection assessed pitch evidence, and spectral template matching among three note classes assessed short-note separability. **Results:** Both executions completed successfully. Under the previously calibrated speed–frequency mapping, repeated harmonic evidence covered discrete target notes from C1 to A6. Low-register interpretation was limited by weak fundamentals and octave ambiguity. At A6, consecutive qualifying spectral-window centers spanned only 80–110 ms; B6 was not reproduced consistently. Notes with a nominal duration of 125 ms achieved approximately 4.5 notes/s, with 31/32 template matches across both experiments. At 100 ms, throughput was 5.21 notes/s with 15/16 matches. The fastest tested condition achieved 8.76 notes/s but only 5/16 matches. **Conclusion:** Within the tested travel envelope and segmented control method, pitch range, stable sounding time, and short-note separability constrain one another. Identification losses were already observed around 4–5 notes/s. Successful movement and high command throughput do not establish equally clear musical performance. These results do not define a universal OT-2 pitch range, perceptual threshold, or firmware limit.

**Keywords:** Opentrons OT-2; motor music; robot acoustics; motion control; harmonic analysis; temporal resolution

## 1 Introduction

Encoding musical notes as motor motion is an unconventional application of robotics and digital fabrication equipment. Existing open-source projects provide MIDI-to-G-code conversion or music workflows for three-dimensional printers [1,2]. These projects establish feasible mappings between motion commands and note sequences, but do not establish that their calibration constants or control strategies transfer directly to liquid-handling robots.

Earlier work in this project demonstrated horizontal circular motion, X/Y speed sweeps, short-melody calibration, and complete robot-side arrangements of *Happy Birthday*, *Jingle Bells*, and *Song of Storms* [4,5]. Changing movement speed changed the spectral structure of the resulting sound. Placing reversals at predefined phrase boundaries allowed complete melodies to fit within a bounded interval. However, maximum movement speed, the highest frequency present in a recording, and the fastest rate at which notes remain distinguishable are different quantities.

This report addresses two operational questions: which target notes produce repeatable spectral evidence within the speed range described as reliable by the manufacturer, and how shortening nominal note duration changes actual execution timing and spectral separability once the complete trajectory has already been composed. Motors are not assumed to be pure-tone sources, and the experiment is not presented as a formal listening evaluation.

## 2 Materials and methods

### 2.1 Equipment, software, and motion constraints

One OT-2 was used, running robot software 26.6.0 and firmware 1.1.0 with protocol API version 2.22. A p300_multi_gen2 pipette was installed on the left mount; the right mount was empty. No tips or liquid handling were involved. Control and recording were performed on a Linux computer.

Opentrons documentation describes the OT-2 default of 400 mm/s as the highest known reliable speed and directs users to contact support before increasing it [3]. Commanded speed was therefore limited to 400 mm/s. Acceleration, motor current, steps/mm, axis limits, and firmware were not changed. This experimental ceiling is not a manufacturer guarantee of musical performance.

The operator-specified X interval was 146.5–246.5 mm, with a planning requirement of at least 5 mm inset at each end. Actual direct-movement endpoints lay within 156.5–236.5 mm, leaving 10 mm at each end; Y was 178.75 mm. Each experiment began with homing, followed by a query of the left pipette's reference-point Z coordinate. All subsequent direct movements used that coordinate. Both experiments reported Z=189.27 mm before and after testing. “Fixed Z” excludes the homing operation and refers to controller-reported position, not an independent displacement measurement.

Before execution, the robot's idle state and installed configuration were checked. The protocol was uploaded and analyzed on the robot, simulated command types, coordinates, speeds, and Z values were checked, and one execution request was sent. The protocol ran on the robot; the network was used for upload and monitoring. Each note still corresponded to an individual `move_to` command. Position queries used the internal read-only `SavePositionParams` interface available in the tested version; compatibility across software versions was not established. Camera input was not used to plan or evaluate motion.

### 2.2 Previous calibration and pitch-range sweeps

Earlier independent speed sweeps and sustained-note measurements provided the following harmonic-spacing model [4]:

`f_model (Hz) = k × v (mm/s), where k = 4.98375 Hz/(mm/s)`.

For MIDI note number m, equal temperament with A4=440 Hz gives:

`f_target = 440 × 2^((m−69)/12), and v = f_target/k`.

This model maps control parameters to targets; it is not a measurement of the fundamental frequency of every movement. Earlier harmonic-based estimates for D2, F2, and D3 were close to their targets, but absolute pitch accuracy traceable to an external frequency standard was not established [4].

The initial experiment contained 14 speed blocks: 0.5, 1, 2, 4, 8, 16, 32, 64, 96, 128, 192, 256, 320, and 400 mm/s. Displacement per stroke was `min(80 mm, v×1.5 s)`. At lower speeds, one stroke was performed in each direction; at speeds of at least 64 mm/s, two strokes were performed in each direction. Strokes were separated by 0.5 s of quiet, and each block began with 2 s of quiet after positioning.

The refinement experiment contained 13 speed blocks: 0.125, 0.25, and 0.5 mm/s, followed by speeds corresponding to C1, C2, C3, C4, C5, C6, E6, G6, A6, and B6. The first three conditions used a nominal movement duration of 3 s; the remaining conditions retained the displacement rule above. Refinement conditions were selected using the initial results. The overall study was exploratory and adaptive, and was not preregistered.

### 2.3 Rhythm sweeps and precomposition

Each rhythm block repeated D2–F2–D3–F2 four times, for 16 notes. Each four-note phrase moved in one direction, and successive phrases reversed direction. All endpoints and directions were calculated and checked before homing. Note displacement equaled commanded speed multiplied by nominal duration. No delays or comments were inserted between notes, so the test characterized short-note behavior under the existing segmented execution method.

Nominal durations in the initial experiment were 1, 0.5, 0.25, 0.125, 0.0625, 0.03125, and 0.015625 s. Refinement durations were 1, 0.5, 0.125, 0.1, and 0.08 s. Within each experiment, the 1 s phrase supplied spectral references and the 0.5 s phrase supplied alignment data; the other conditions were evaluated against them. Note order was fixed, without randomization.

### 2.4 Recording and temporal alignment

A headset microphone connected to the Linux computer was placed near the robot. PipeWire recorded mono, 16-bit PCM audio at 48 kHz. Input volume was 0.20, with Headset Mic Boost set to 0 dB. The microphone model and its precise distance and orientation were not recorded, preventing direct comparisons of loudness across laboratories. The sampling clock was not checked against an external frequency standard, and sound pressure level was not calibrated.

The robot and computer clocks differed substantially. Clock samples were collected before and after each experiment; the sample with the lowest round-trip latency supplied the initial conversion. Recording start time was estimated from the end time and sample count. An additional offset from −100 to +220 ms was then searched in 5 ms steps using the 0.5 s calibration phrase. Five positions within each command interval—10%, 30%, 50%, 70%, and 90%—were evaluated, and the offset maximizing template agreement was selected. The resulting offsets were +65 ms for the initial experiment and +70 ms for refinement, with calibration-frame agreement of 97.5% and 100%, respectively. These offsets absorb several timing errors and are not measurements of acoustic propagation delay.

### 2.5 Pitch-range detection

Hann-window FFTs and parabolic interpolation of log magnitude were used to examine harmonics 1–8, 16, 32, and 64 of the modeled frequency. Candidate target components were restricted to 70–6000 Hz. A 240 ms window was used below 300 Hz. For other components, the window was 120 ms at speeds below 128 mm/s and 40 ms otherwise. The hop was 40 ms at lower speeds and 10 ms at higher speeds. Each window lay completely within the aligned command interval.

For each frame, a local peak was selected within ±6% of the target. The interpolated frequency then had to lie within 25 cents of the target, exceed the pre-block quiet reference by at least 10 dB, and exceed the median local spectrum by at least 8 dB. The local neighborhood had half-width `max(200 Hz, 0.25×target frequency)`, excluding the target search band. Frequency error in cents was defined as `1200×log2(f_measured/f_target)`.

Consecutive qualifying window centers had to span at least `max(40 ms, window length/2)`. The reported span is not an independently measured constant-speed plateau. Spectral windows can include acceleration or deceleration. This procedure is target-conditioned harmonic verification: the false-positive rate over the full search space was not measured, and a unique perceived fundamental was not established. Low-frequency inference requires multiple harmonics and both movement directions, rather than assigning a note from one high-order spectral line.

### 2.6 Timing metrics and note classification

Command onset intervals were differences between successive movement `startedAt` timestamps, yielding 15 intervals per block. Block duration extended from `BLOCK_BEGIN.completedAt` to `BLOCK_END.startedAt`. Throughput was 16 divided by block duration and included a small amount of within-block scheduling overhead. It is distinct from the reciprocal of the median onset interval and from acoustic onset detection for individual notes.

Reference-note features were sampled from 0.3 s after command start to 0.2 s before command completion, at 40 ms steps. Features used 40 ms Hann windows and the 100–3000 Hz band. Quiet-reference power was subtracted, negative values were clipped to zero, and the square root was taken before normalization. Feature vectors were averaged within each reference note and normalized again. A test window was compared with reference templates using cosine similarity. The maximum similarity within each class was used, and the highest-scoring class among D2, F2, and D3 was selected. The 1 s reference self-check excluded the template of the note being classified.

For faster blocks, one window was taken at each aligned command midpoint, without further template or offset adjustment. Counts indicate agreement with the intended sequence, not human listening accuracy. Classes were imbalanced: four D2, eight F2, and four D3 notes per block. Always predicting F2 would yield 8/16 agreement.

Measurements shared a device, recording, templates, and repeated phrase structure. Only descriptive statistics and explicit denominators are therefore reported. No significance tests were performed, and independent binomial confidence intervals were not used to imply an independent sample size.

## 3 Results

### 3.1 Execution and geometric verification

All 287 commands in the initial experiment succeeded, including 175 direct movements. All 235 commands in refinement succeeded, including 136 direct movements. Both final execution states were `succeeded`, with empty error lists. All direct-movement commands satisfied the speed and coordinate constraints, and initial and final Z queries agreed. Successful execution supports completion of the control workflow; it does not independently rule out small missed steps, long-term wear, or acoustic error.

### 3.2 Pitch evidence and temporal persistence

Table 1 lists standard-note targets from refinement. Target frequencies and speeds were calculated from the model; measured frequencies came from qualifying spectral windows. In the lower register, the strongest spectral line was not automatically assigned as the fundamental.

**Table 1. Discrete target notes and recorded evidence.**

| Target | Target Hz | Speed mm/s | Main observation |
|---|---:|---:|---|
| C1 | 32.703 | 6.562 | Both directions showed components near 97.7, 130.5, and 521.9 Hz; the fundamental was inferred from harmonics |
| C2 | 65.406 | 13.124 | Both directions showed components near 130.8, 326.9, 522.9, and 1045.9 Hz |
| C3 | 130.813 | 26.248 | Repeatable harmonics in both directions; the target fundamental met persistence criteria in only one direction |
| C4 | 261.626 | 52.496 | Repeatable harmonics in both directions; the target fundamental met persistence criteria in only one direction |
| C5 | 523.251 | 104.991 | All four strokes: 523.1–523.2 Hz; window-center span approximately 720 ms |
| C6 | 1046.502 | 209.983 | All four strokes: 1045.6–1046.8 Hz; span 290–300 ms |
| E6 | 1318.510 | 264.562 | All four strokes: 1316.6–1317.3 Hz; span 160–180 ms |
| G6 | 1567.982 | 314.619 | All four strokes: 1560.0–1568.2 Hz; span 100–140 ms |
| A6 | 1760.000 | 353.148 | All four strokes: 1752.4–1761.6 Hz; span 80–110 ms |
| B6 | 1975.533 | 396.395 | The target fundamental did not pass; only brief higher harmonics appeared in some repetitions |

<!-- FIGURE_RANGE -->

**Figure 1. Frequency and persistence of target components in the upper register.** Points show individual strokes, with blue indicating positive and orange negative X motion; lines indicate target frequencies. The second panel shows consecutive qualifying window-center spans. B6 failed the criterion and is marked as missing, not as a zero-frequency or zero-duration observation. The 40 ms analysis window limits interpretation of very short stable segments.

A6 was the highest tested standard note that passed. A♯6 was not tested, so A6 cannot be treated as the exact boundary. The initial experiment's modeled target of approximately 1993.5 Hz at 400 mm/s was also not reproduced consistently. C1 to A6 spans five octaves and nine semitones, but this is the coverage of discrete tested targets, not a continuous perceptual range verified at every semitone.

At the low end, 0.125, 0.25, and 0.5 mm/s did not pass the criteria. At 1–2 mm/s, detections were predominantly high-order harmonics with ambiguous interpretation. At 4 mm/s, several components were consistent with a modeled fundamental of approximately 19.935 Hz, but did not establish a clear 20 Hz note. The perceptual lower boundary remains undetermined.

### 3.3 Nominal duration, actual throughput, and feature separability

**Table 2. Fast-note conditions. Each row contains 16 notes; onset-interval statistics use 15 intervals.**

| Nominal ms | Experiment | Median interval ms | Throughput notes/s | Template agreement |
|---:|---|---:|---:|---:|
| 250 | Initial | 345 | 2.89 | 16/16 |
| 125 | Initial | 222 | 4.51 | 16/16 |
| 125 | Refinement | 214 | 4.54 | 15/16 |
| 100 | Refinement | 190 | 5.21 | 15/16 |
| 80 | Refinement | 171 | 5.84 | 12/16 |
| 62.5 | Initial | 154 | 6.50 | 10/16 |
| 31.25 | Initial | 123 | 7.87 | 10/16 |
| 15.625 | Initial | 110 | 8.76 | 5/16 |

<!-- FIGURE_RHYTHM -->

**Figure 2. Nominal note duration, execution timing, and spectral classification.** The panels compare actual command intervals with nominal durations and show template agreement against block throughput. Symbols distinguish the two experiments. The dashed 50% line is the majority-class baseline, not a statistical significance threshold. The 1 s reference and 0.5 s alignment conditions are excluded from the fast-note classification panel.

The two 125 ms conditions yielded 31/32 matches together; the 100 ms condition yielded 15/16, falling to 12/16 at 80 ms. Although the 15.625 ms condition had the highest throughput, its 5/16 matches were below the majority-class baseline. This indicates that the present template method lost useful identification ability for extremely short notes; it does not establish that every listener would fail to distinguish them.

The difference between nominal duration and actual interval was approximately 90–100 ms, and the fastest median actual interval remained approximately 110 ms. Precomposition removed per-note host network requests but did not eliminate segmented execution overhead or acceleration and deceleration effects.

Using block throughput, approximately 4.5–5.2 notes/s corresponds to continuous eighth notes at about 135–156 BPM, or continuous sixteenth notes at about 68–78 BPM. The conversion is `BPM = 60 × notes/s ÷ notes per beat`. A tempo limit must specify note value rather than report a single “maximum BPM.”

## 4 Discussion

### 4.1 Coupling between pitch range and travel

Higher-frequency targets required higher speeds, while the fixed 80 mm stroke shortened nominal movement duration as speed increased. For A6, the nominal stroke lasted approximately 80/353.148=0.227 s, but qualifying spectral-window centers covered only about 0.1 s. Reaching a high-note condition and sustaining it are therefore not interchangeable. The observations are consistent with acceleration constraints in bounded travel, but velocity trajectories were not independently measured; B6 failure cannot be attributed entirely to acceleration.

Increasing travel, using another axis, or changing the control method might change the outcome, but none was tested here. The manufacturer's 400 mm/s reliability statement also does not establish a reliable musical upper limit near 2 kHz.

### 4.2 Harmonics, octave ambiguity, and pitch accuracy

Motor motion produced multiple speed-dependent components, with low-register fundamentals potentially weaker than higher harmonics. The harmonic model supports relative frequency organization, but perception may involve octave substitution, additional pitches, or a pronounced mechanical timbre. Target-conditioned detection also introduces prior-selection bias. C1–A6 should consequently be interpreted as repeated spectral structures consistent with the tested targets, not a demonstrated range of clear pure tones.

Decimal places in the tables support parameter reproduction and arithmetic checks. An uncalibrated sampling clock, limited signal-to-noise ratio, finite FFT windows, and peak interpolation all affect absolute-frequency interpretation. Numerical precision should not be equated with acoustic measurement accuracy.

### 4.3 From command throughput to musical tempo

Some template errors were already present around 4–5 notes/s, whereas all notes matched in the 250 ms condition at approximately 2.9 notes/s. Future arrangements can therefore use about 3 notes/s as a more conservative tested operating point and treat about 4–5 notes/s as a marginal region requiring listening validation, rather than a guarantee.

The experiment used only three notes, fixed four-note phrases, and reversals every four notes. Short-note spectra may depend jointly on pitch, acceleration, deceleration, and direction changes. No randomized factorial experiment was performed to separate these effects. The observed classification performance cannot be transferred directly to a full scale, other registers, repeated identical notes, or different articulation gaps.

### 4.4 Limitations and further experiments

Only one robot was studied in two experiments on the same day. Upper-register conditions generally had four strokes each, and fast-note conditions had sixteen notes each. Observations were dependent, without cross-day replication. Refinement conditions were selected from the initial results and therefore provide exploratory evidence. Microphone placement was not quantified. There was no formal blind listening test, external position or velocity measurement, sound-pressure calibration, or long-term durability evaluation.

A generalizable usable range would require semitone-by-semitone sweeps with fixed microphone placement, multiple devices and dates, recorded velocity trajectories, and predefined persistence requirements. Perceptually distinguishable tempo should be assessed with balanced randomized note sequences, independent training and test recordings, fundamental-frequency estimation without target cues, and blind listening. These validations were not completed in this study.

## 5 Conclusion

Two experiments characterized OT-2 motor music within the manufacturer's stated reliable speed range and a bounded travel interval. Repeated harmonic evidence covered discrete standard-note targets from C1 to A6, but low-register interpretation depended on harmonics and high-register persistence was short; B6 was not reproduced consistently. Identification losses appeared around 4–5 notes/s, and the fastest throughput of 8.76 notes/s did not provide equivalent note separability. Control and arrangement should jointly account for spectral structure, persistence, travel boundaries, and segmented execution time.

## Data, code, and reproducibility

The repository contains the two executed protocols, offline analysis code, a reviewed compact result dataset at `docs/research/data/evidence.json`, and figure/report build scripts. The dataset retains per-note command times, template predictions, qualifying harmonics for individual movements, and SHA-256 hashes of original source files. Figures can be rebuilt from this dataset alone; spectral re-extraction additionally requires the original local WAV files and execution records.

Reviewed Chinese and English article PDFs are distributed in `docs/research/pdf/`. Original recordings, individual HTTP logs, runtime environments, and intermediate build products remain in Git-ignored local directories. Audio is not an open dataset. File hashes support later verification but do not make the missing source data downloadable. The absence of original audio limits independent external reanalysis, and the report does not claim complete open-data reproducibility.

The experiments are labeled “Initial” and “Refinement.” Actual device, protocol, analysis, and execution identifiers are excluded from the publication. Detailed methods and results are recorded in [6]. Dates follow the control computer, with robot clock differences handled as described above.

AI assisted manuscript preparation, protocol implementation, and analysis organization. Authorship, affiliation, funding, and competing-interest declarations should be supplied by the responsible researcher before formal submission; none has been assigned on their behalf. This report has not been submitted to a journal or peer reviewed.

## References

1. nescio007. *midi2gcode: A MIDI to G-code converter*. Open-source software repository. https://github.com/nescio007/midi2gcode (accessed 14 September 2026).
2. Toglefritz. *Musical Marlin: Make your 3D printer play music*. Open-source software repository. https://github.com/Toglefritz/Musical_Marlin (accessed 14 September 2026).
3. Opentrons. *Python API: Labware and Deck Positions — Gantry Speed*. Official technical documentation. https://docs.opentrons.com/python-api/robot-position/#gantry-speed (accessed 14 September 2026).
4. Opentrons AI project records. [OT-2 motor-pitch calibration and Song of Storms listening samples](../ot2-pitch-calibration-results.md). 14 September 2026. Project technical record in Chinese; not peer reviewed.
5. Opentrons AI project records. [Complete motor music arrangements](../ot2-music-full-arrangements.md). 14 September 2026. Project technical record.
6. Opentrons AI project records. [OT-2 pitch-range and rhythm measurements](../ot2-music-limits.md). 14 September 2026. Project record in Chinese, including criteria and anonymized execution results.
