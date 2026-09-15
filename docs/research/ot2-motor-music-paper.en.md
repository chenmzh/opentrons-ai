# Human–AI Co-Development of OT-2 Motor Music through Acoustic Feedback: Architecture, Decision Roles, and an Exploratory Case Study

**Mingzhe Chen**

Correspondence: [cmzcswxp@gmail.com](mailto:cmzcswxp@gmail.com)

Study type: retrospective human–AI co-development case study with single-device acoustic experiments. Experiment dates: 14–15 September 2026 (control computer). Manuscript revision: 15 September 2026. Version: 2.0 draft. Project: Opentrons AI. Not submitted or peer reviewed.

## Abstract

Motor-generated music provides a measurable physical task for studying how a language-model agent, an operator, and numerical tools cooperate. We describe a human–AI workflow that developed musical motion on an unmodified Opentrons OT-2 using acoustic feedback between experimental rounds. The operator defined musical goals, arranged microphone access, specified motion constraints, and proposed phrase-boundary reversals and whole-score precomposition. The agent implemented protocols, invoked measurement tools, interpreted spectra, and revised subsequent experiments. Deterministic code compiled bounded trajectories and checked commands; robot-side execution remained segmented and had no online acoustic pitch correction. A documented calibration episode changed from tracking a prominent speed-dependent spectral line to a harmonic-spacing interpretation after competing components were observed. Subsequent pitch-range and rhythm experiments comprised 27 speed blocks, 12 rhythm blocks, and 311 direct movements. Repeated harmonic evidence covered discrete targets from C1 to A6, with weak-fundamental ambiguity at low frequencies and only 80–110 ms of qualifying window-center persistence at A6. Nominal 125 ms notes achieved approximately 4.5 notes/s and 31/32 template matches across two experiments; the fastest condition achieved 8.76 notes/s with 5/16 matches. These measurements characterize the physical task, not a causal benefit of AI. The contribution is an inspectable case study of acoustic feedback, constrained precomposition, and explicit human decision roles. A next-day held-out test under an injected 8% mapping error yielded 8/12 estimates within ±25 cents after numerical feedback versus 0/12 with the frozen mapping; four feedback estimates remained uncertain. No LLM-versus-conventional-calibration comparison was performed, and autonomous operation, perceptual pitch accuracy, and generalization remain unestablished.

**Keywords:** human–AI collaboration; language-model agents; acoustic feedback; motor music; constrained motion planning; experimental calibration

## 1 Introduction and related work

Motor music couples a symbolic specification—a score—to a physical outcome that can be recorded and measured. MIDI-to-G-code and printer-music projects already demonstrate this general application [1,2]. A liquid-handling robot offers an additional constraint: notes must be realized through an existing motion API within a bounded workspace, without modifying the drive electronics. The resulting sound contains multiple spectral components, so successful motion alone does not establish correct musical output.

Acoustic feedback in musical robotics and feedback-guided language-model planning both precede this work. The Closed-Loop Robotic Glockenspiel used embedded musical information retrieval for unaided recalibration and latency compensation [7]. Inner Monologue examined language-model planning with environmental and human feedback [8], while BrainBody-LLM used closed-loop state feedback to correct robot plans [9]. We therefore make no claim to invent acoustic feedback, LLM feedback loops, or motor music. The selected references establish relevant precedents; they do not constitute a systematic novelty search.

This study examines how these ideas were combined in one operator–agent session: the human specified goals and revised the problem, the agent translated those instructions into experiments and code, and acoustic measurements informed later decisions. The central question is how to separate these contributions and distinguish an experiment-level feedback loop from a finished autonomous controller. A second question concerns the physical limits encountered when complete musical trajectories are composed before execution.

We contribute (i) a description of the implemented workflow and its control boundaries; (ii) a retrospective account attributing specific decisions to the human, agent, and deterministic tools; and (iii) descriptive acoustic and timing measurements with explicit limitations. This is a situated engineering case study, not a benchmark establishing that AI improves calibration. Workflow attribution uses the operator instructions retained in the project conversation together with technical records [4–6,10]; it was not independently coded or evaluated as a human-subject study.

## 2 Architecture and human participation

### 2.1 Components and information flow

The implemented architecture has five functional components (Figure 1). A human operator communicates goals and constraints in natural language. A tool-using coding agent works in the shared repository and invokes shell/Python tools to generate protocols, run checks, collect measurements, and inspect numerical results. Deterministic composition and validation code translates a score into bounded movements. The host transport uploads a protocol and monitors robot-side execution. A microphone and offline signal-processing tools return acoustic measurements to the agent for the next experimental decision. These are functional responsibilities, not five independently deployed services.

<!-- FIGURE_ARCHITECTURE -->

**Figure 1. Implemented human–AI experimental workflow.** Solid arrows show instructions, executable artifacts, motion, and measurements. The returning measurement path closes the loop between experiments through the agent. The operator supplies goals and revisions, receives reports, and provides physical setup; no mandatory human approval after every note or experiment is implied. Compilation, transport, robot execution, and acoustic analysis are deterministic tools. No audio feedback enters a playing protocol, and no camera input enters the decision path.

The agent operated through the coding-session interface. The repository does not contain a standalone LLM service that automatically repeats this whole loop, and the observation dashboard is not its execution front end. Published song launchers can execute a precomposed score without an LLM or microphone. Earlier recording helpers remain local experimental tools. This separation matters: reproducible playback code is available, while reproduction of the complete conversational development process requires additional agent/session information.

### 2.2 What is closed, and at what timescale?

The acoustic loop follows: propose an experiment, execute and record, extract spectral evidence, interpret the evidence, change a later protocol or mapping, and test again. Feedback changes subsequent actions, which distinguishes this process from recording solely for documentation. Here, updates occurred between completed experimental rounds. No per-note or millisecond-scale feedback controller was implemented, and no convergence rate for repeated automatic pitch correction was measured.

The agent consumed tool-produced frequencies, harmonic evidence, and command results. We do not claim that a multimodal model directly listened to the waveform or made a validated perceptual judgment. FFT analysis and template matching supplied the measurements; the agent supplied interpretation and code changes. Conversation context and saved artifacts carried prior observations between steps. There was no task-specific model training or demonstrated online weight update.

A separate execution-checking path compared simulated and recorded commands with allowed motion. For the song launchers, checks cover installed configuration, robot availability, command types, endpoint coordinates, speeds, and fixed post-home Z. A local controller lock reduces conflicts between copies of that launcher; it does not exclude every possible external robot client. These checks constrain this implementation and do not constitute a formal safety proof or an isolated runtime sandbox around arbitrary agent-generated code.

### 2.3 The human's scientific and engineering role

**Table 1. Observed division of work, reconstructed from operator instructions and project records [4–6,10].**

| Activity | Human contribution | Agent/tool contribution |
|---|---|---|
| Problem formulation | Noticed changing motor pitch; selected melodies; requested calibration and limits testing | Searched precedents; translated goals into candidate protocols and measurements |
| Physical setup and scope | Specified no tips, fixed Z, moderate initial speed; connected a headset microphone to the Linux host and made it available near the robot | Diagnosed recording access, invoked capture tools, and checked controller-reported configuration |
| Motion design | Proposed changing direction between phrases; requested whole-score precomposition; clarified a 100 mm interval with a 5 mm inset | Implemented bounded phrase planning, direction search, coordinate checks, and standalone launchers |
| Interpretation and acceptance | Prioritized relative pitch and requested complete arrangements; supplied informal feedback that playback seemed fluent | Reported spectral ambiguity, revised the model/register, and selected refinement measurements |
| Research framing and dissemination | Raised AI-in-the-loop as the research question; requested architecture and contribution attribution; specified publication exclusions | Organized evidence, drafted the manuscript, and generated figures and bilingual documents |

The human therefore influenced the objective, feasible operating conditions, and algorithmic design. In particular, phrase-level reversal and precomposition originated in operator suggestions; they should not be attributed to autonomous agent discovery. Physical microphone setup also depended on the operator. Their comment about fluency is qualitative session feedback, not a blinded listening result. Conversely, the record does not show a human manually choosing every numerical speed, interpreting every spectrum, or approving every command. We describe shared development without assigning unsupported percentages of effort or autonomy.

### 2.4 Deterministic precomposition and execution

For each note i, the compiler maps the target frequency to speed using the calibrated factor k, computes nominal duration from tempo and beat value, deducts any articulation gap, and sets displacement `d_i = v_i × t_sound,i`. For phrase j, `D_j = sum(d_i)` is its monotonic travel. The planner searches directions `s_j` in {−1,+1}, forms cumulative phrase endpoints, and rejects paths whose span exceeds the allowed width `W = x_max − x_min − 2 × margin`. Feasible paths are ranked first by reversal count, then by occupied span, and translated to center their extrema in the interval. Every note endpoint is checked before motion.

The current song implementation enumerates at most 16 phrases, fixing the first direction to remove mirror symmetry. This is a small deterministic search, not a learned planner or a scalable optimization contribution. A phrase that cannot fit is rejected so its arrangement can be revised before execution. Whole-score upload removes per-note host requests; robot-side `move_to` calls remain separate segments. The song-specific speed caps are 30 or 36 mm/s. The separate range experiments described below reached 400 mm/s; the song launcher's validator is not used to authorize that wider range.

## 3 Materials and methods

Sections 3.1–3.6 describe the 14 September range and rhythm experiments; Section 3.7 describes the separately planned 15 September feedback supplement.

### 3.1 Equipment, software, and motion constraints

One OT-2 was used, running robot software 26.6.0 and firmware 1.1.0 with protocol API version 2.22. A p300_multi_gen2 pipette was installed on the left mount; the right mount was empty. No tips or liquid handling were involved. Control and recording were performed on a Linux computer.

Opentrons documentation describes the OT-2 default of 400 mm/s as the highest known reliable speed and directs users to contact support before increasing it [3]. Commanded speed was therefore limited to 400 mm/s. Acceleration, motor current, steps/mm, axis limits, and firmware were not changed. This experimental ceiling is not a manufacturer guarantee of musical performance.

The operator-specified X interval was 146.5–246.5 mm, with a planning requirement of at least 5 mm inset at each end. Actual direct-movement endpoints lay within 156.5–236.5 mm, leaving 10 mm at each end; Y was 178.75 mm. Each experiment began with homing, followed by a query of the left pipette's reference-point Z coordinate. All subsequent direct movements used that coordinate. Both experiments reported Z=189.27 mm before and after testing. “Fixed Z” excludes the homing operation and refers to controller-reported position, not an independent displacement measurement.

Before execution, the robot's idle state and installed configuration were checked. The protocol was uploaded and analyzed on the robot, simulated command types, coordinates, speeds, and Z values were checked, and one execution request was sent. The protocol ran on the robot; the network was used for upload and monitoring. Each note still corresponded to an individual `move_to` command. Position queries used the internal read-only `SavePositionParams` interface available in the tested version; compatibility across software versions was not established. Camera input was not used to plan or evaluate motion.

### 3.2 Previous calibration and pitch-range sweeps

Earlier independent speed sweeps and sustained-note measurements provided the following harmonic-spacing model [4]:

`f_model (Hz) = k × v (mm/s), where k = 4.98375 Hz/(mm/s)`.

For MIDI note number m, equal temperament with A4=440 Hz gives:

`f_target = 440 × 2^((m−69)/12), and v = f_target/k`.

This model maps control parameters to targets; it is not a measurement of the fundamental frequency of every movement. Earlier harmonic-based estimates for D2, F2, and D3 were close to their targets, but absolute pitch accuracy traceable to an external frequency standard was not established [4].

The initial experiment contained 14 speed blocks: 0.5, 1, 2, 4, 8, 16, 32, 64, 96, 128, 192, 256, 320, and 400 mm/s. Displacement per stroke was `min(80 mm, v×1.5 s)`. At lower speeds, one stroke was performed in each direction; at speeds of at least 64 mm/s, two strokes were performed in each direction. Strokes were separated by 0.5 s of quiet, and each block began with 2 s of quiet after positioning.

The refinement experiment contained 13 speed blocks: 0.125, 0.25, and 0.5 mm/s, followed by speeds corresponding to C1, C2, C3, C4, C5, C6, E6, G6, A6, and B6. The first three conditions used a nominal movement duration of 3 s; the remaining conditions retained the displacement rule above. Refinement conditions were selected using the initial results. The overall study was exploratory and adaptive, and was not preregistered.

### 3.3 Rhythm sweeps and precomposition

Each rhythm block repeated D2–F2–D3–F2 four times, for 16 notes. Each four-note phrase moved in one direction, and successive phrases reversed direction. All endpoints and directions were calculated and checked before homing. Note displacement equaled commanded speed multiplied by nominal duration. No delays or comments were inserted between notes, so the test characterized short-note behavior under the existing segmented execution method.

Nominal durations in the initial experiment were 1, 0.5, 0.25, 0.125, 0.0625, 0.03125, and 0.015625 s. Refinement durations were 1, 0.5, 0.125, 0.1, and 0.08 s. Within each experiment, the 1 s phrase supplied spectral references and the 0.5 s phrase supplied alignment data; the other conditions were evaluated against them. Note order was fixed, without randomization.

### 3.4 Recording and temporal alignment

A headset microphone connected to the Linux computer was placed near the robot. PipeWire recorded mono, 16-bit PCM audio at 48 kHz. Input volume was 0.20, with Headset Mic Boost set to 0 dB. The microphone model and its precise distance and orientation were not recorded, preventing direct comparisons of loudness across laboratories. The sampling clock was not checked against an external frequency standard, and sound pressure level was not calibrated.

The robot and computer clocks differed substantially. Clock samples were collected before and after each experiment; the sample with the lowest round-trip latency supplied the initial conversion. Recording start time was estimated from the end time and sample count. An additional offset from −100 to +220 ms was then searched in 5 ms steps using the 0.5 s calibration phrase. Five positions within each command interval—10%, 30%, 50%, 70%, and 90%—were evaluated, and the offset maximizing template agreement was selected. The resulting offsets were +65 ms for the initial experiment and +70 ms for refinement, with calibration-frame agreement of 97.5% and 100%, respectively. These offsets absorb several timing errors and are not measurements of acoustic propagation delay.

### 3.5 Pitch-range detection

Hann-window FFTs and parabolic interpolation of log magnitude were used to examine harmonics 1–8, 16, 32, and 64 of the modeled frequency. Candidate target components were restricted to 70–6000 Hz. A 240 ms window was used below 300 Hz. For other components, the window was 120 ms at speeds below 128 mm/s and 40 ms otherwise. The hop was 40 ms at lower speeds and 10 ms at higher speeds. Each window lay completely within the aligned command interval.

For each frame, a local peak was selected within ±6% of the target. The interpolated frequency then had to lie within 25 cents of the target, exceed the pre-block quiet reference by at least 10 dB, and exceed the median local spectrum by at least 8 dB. The local neighborhood had half-width `max(200 Hz, 0.25×target frequency)`, excluding the target search band. Frequency error in cents was defined as `1200×log2(f_measured/f_target)`.

Consecutive qualifying window centers had to span at least `max(40 ms, window length/2)`. The reported span is not an independently measured constant-speed plateau. Spectral windows can include acceleration or deceleration. This procedure is target-conditioned harmonic verification: the false-positive rate over the full search space was not measured, and a unique perceived fundamental was not established. Low-frequency inference requires multiple harmonics and both movement directions, rather than assigning a note from one high-order spectral line.

### 3.6 Timing metrics and note classification

Command onset intervals were differences between successive movement `startedAt` timestamps, yielding 15 intervals per block. Block duration extended from `BLOCK_BEGIN.completedAt` to `BLOCK_END.startedAt`. Throughput was 16 divided by block duration and included a small amount of within-block scheduling overhead. It is distinct from the reciprocal of the median onset interval and from acoustic onset detection for individual notes.

Reference-note features were sampled from 0.3 s after command start to 0.2 s before command completion, at 40 ms steps. Features used 40 ms Hann windows and the 100–3000 Hz band. Quiet-reference power was subtracted, negative values were clipped to zero, and the square root was taken before normalization. Feature vectors were averaged within each reference note and normalized again. A test window was compared with reference templates using cosine similarity. The maximum similarity within each class was used, and the highest-scoring class among D2, F2, and D3 was selected. The 1 s reference self-check excluded the template of the note being classified.

For faster blocks, one window was taken at each aligned command midpoint, without further template or offset adjustment. Counts indicate agreement with the intended sequence, not human listening accuracy. Classes were imbalanced: four D2, eight F2, and four D3 notes per block. Always predicting F2 would yield 8/16 agreement.

Measurements shared a device, recording, templates, and repeated phrase structure. Only descriptive statistics and explicit denominators are therefore reported. No significance tests were performed, and independent binomial confidence intervals were not used to imply an independent sample size.

### 3.7 Next-day supplementary acoustic-feedback validation

On 15 September 2026, a separate calibration recording and held-out comparison were performed on the same robot after a written plan and the estimator source had been frozen locally [11]. This was not registry preregistration. An 8% error was deliberately injected into the prior mapping, giving `k_initial = 5.38245 Hz/(mm/s)`; under an unchanged linear relation this predicts approximately −133.2 cents. The perturbation was a software challenge, not evidence of hardware drift. C4, E4, and G4 were each measured twice in each direction (12 calibration strokes). A conventional update took the median of accepted frequency/speed ratios, requiring at least two accepted observations per calibration note and both directions. The agent reviewed the result and selected the prescribed update without manual octave correction.

The second recording interleaved D4, F4, and A4 under the initial and fitted mappings, twice in each direction (24 strokes; 12 per condition). These notes were excluded from this calibration recording, although the agent already knew the earlier project mapping; the experiment was not a blind test of an agent with no prior knowledge. Calibration and test order used fixed random seeds 20260915 and 20260916. Each 70 mm measurement stroke used endpoints 161.5 and 231.5 mm, preceded by positioning at 30 mm/s and 0.9 s quiet, and followed by 0.6 s quiet. The separate validator capped speed at 110 mm/s; actual measurement speeds did not exceed 88.292 mm/s. Robot-side simulation and exact trajectory checks preceded execution. All movements after homing retained Y=178.75 mm and the measured home Z.

The default headset microphone recorded 48 kHz, mono, 16-bit audio. A central 0.4 s window was extracted for each measurement using the minimum-round-trip host/robot clock-offset sample and the recording-start estimate. No target-based alignment adjustment was made. The estimated alignment uncertainty was ±0.15 s; microphone geometry and sampling-clock accuracy remained uncalibrated. The fixed pitch estimator received waveform samples and sample rate only, not the intended note or speed. It searched 180–650 Hz fundamentals using up to six harmonics. Candidate peaks required at least 12 dB local prominence and amplitude within 35 dB of the strongest spectral bin. Harmonic matches used an 18-cent tolerance, required at least three harmonics including an odd harmonic, and were scored by summed prominence capped at 45 dB per harmonic. A competing candidate more than 50 cents away with at least 90% of the best score made the estimate uncertain. The output frequency was the median of the matched peak frequencies divided by harmonic number. Synthetic missing-fundamental and insufficient-evidence cases were checked before recording. This register-limited estimator is not general-purpose transcription and may still select an octave-shifted interpretation.

The primary endpoint was the number of all scheduled held-out strokes with an accepted estimate within ±25 cents of the target. Uncertain estimates remained failures in that denominator. Median absolute cents error was also reported, explicitly conditional on accepted estimates. The coefficient, windowing, detector, and scoring rule were unchanged after the held-out recording; neither recording was repeated to select a favorable outcome. This comparison evaluates measurement-based numerical feedback versus a frozen perturbed mapping, not the incremental benefit of an LLM over a conventional fitter.

## 4 Results

### 4.1 Recorded feedback and design episodes

**Table 2. Evidence of iteration and its interpretation. The episodes are retrospective summaries, not independent trials or a complete timestamped agent trace.**

| Episode | Evidence and action | Supported interpretation |
|---|---|---|
| Initial speed mapping | X-axis sweeps yielded a tracked-line ratio near 79.74 Hz/(mm/s); sustained D4–F4–D5 measurements revealed competing components, including a strong component near 329 Hz [4] | A near-target spectral line did not by itself establish an unambiguous musical pitch |
| Revised acoustic interpretation | A later protocol used the 4.98375 Hz/(mm/s) harmonic-spacing model and D2–F2–D3; a separate recording checked integer-related components [4] | The agent-led revision used measured evidence and was retested; it did not establish superior perceived tuning |
| Human-guided motion revision | The operator proposed phrase-boundary reversals and precomposition; the resulting three arrangements completed robot execution with checked geometry [5,10] | Human design input was implemented successfully; these full-song runs had no audio recording and establish no measured acoustic improvement |
| Adaptive limit testing | Initial results informed the standard-note sweep and added rhythm conditions at 125, 100, and 80 ms [6] | Measurements influenced follow-up sampling; efficiency relative to fixed sweeps was not tested |

In the revised three-note calibration, harmonic-inferred frequency errors were approximately −1.5, −0.4, and −1.1 cents for D2, F2, and D3. They are model-dependent estimates from different notes/registers than the first version, not a paired before/after demonstration of AI improvement. Weak fundamentals and octave ambiguity remained [4].

The acoustic experiments below characterize the resulting operating regime. Their 311 movements do not include the earlier calibration or the three complete-song demonstrations. All belong to one device and one co-development context; movements and notes are not independent agent-development sessions.

### 4.2 Execution and geometric verification

All 287 commands in the initial experiment succeeded, including 175 direct movements. All 235 commands in refinement succeeded, including 136 direct movements. Both final execution states were `succeeded`, with empty error lists. All direct-movement commands satisfied the speed and coordinate constraints, and initial and final Z queries agreed. Successful execution supports completion of the control workflow; it does not independently rule out small missed steps, long-term wear, or acoustic error.

### 4.3 Pitch evidence and temporal persistence

Table 3 lists standard-note targets from refinement. Target frequencies and speeds were calculated from the model; measured frequencies came from qualifying spectral windows. In the lower register, the strongest spectral line was not automatically assigned as the fundamental.

**Table 3. Discrete target notes and recorded evidence.**

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

**Figure 2. Frequency and persistence of target components in the upper register.** Points show individual strokes, with blue indicating positive and orange negative X motion; lines indicate target frequencies. The second panel shows consecutive qualifying window-center spans. B6 failed the criterion and is marked as missing, not as a zero-frequency or zero-duration observation. The 40 ms analysis window limits interpretation of very short stable segments.

A6 was the highest tested standard note that passed. A♯6 was not tested, so A6 cannot be treated as the exact boundary. The initial experiment's modeled target of approximately 1993.5 Hz at 400 mm/s was also not reproduced consistently. C1 to A6 spans five octaves and nine semitones, but this is the coverage of discrete tested targets, not a continuous perceptual range verified at every semitone.

At the low end, 0.125, 0.25, and 0.5 mm/s did not pass the criteria. At 1–2 mm/s, detections were predominantly high-order harmonics with ambiguous interpretation. At 4 mm/s, several components were consistent with a modeled fundamental of approximately 19.935 Hz, but did not establish a clear 20 Hz note. The perceptual lower boundary remains undetermined.

### 4.4 Nominal duration, actual throughput, and feature separability

**Table 4. Fast-note conditions. Each row contains 16 notes; onset-interval statistics use 15 intervals.**

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

**Figure 3. Nominal note duration, execution timing, and spectral classification.** The panels compare actual command intervals with nominal durations and show template agreement against block throughput. Symbols distinguish the two experiments. The dashed 50% line is the majority-class baseline, not a statistical significance threshold. The 1 s reference and 0.5 s alignment conditions are excluded from the fast-note classification panel.

The two 125 ms conditions yielded 31/32 matches together; the 100 ms condition yielded 15/16, falling to 12/16 at 80 ms. Although the 15.625 ms condition had the highest throughput, its 5/16 matches were below the majority-class baseline. This indicates that the present template method lost useful identification ability for extremely short notes; it does not establish that every listener would fail to distinguish them.

The difference between nominal duration and actual interval was approximately 90–100 ms, and the fastest median actual interval remained approximately 110 ms. Precomposition removed per-note host network requests but did not eliminate segmented execution overhead or acceleration and deceleration effects.

Using block throughput, approximately 4.5–5.2 notes/s corresponds to continuous eighth notes at about 135–156 BPM, or continuous sixteenth notes at about 68–78 BPM. The conversion is `BPM = 60 × notes/s ÷ notes per beat`. A tempo limit must specify note value rather than report a single “maximum BPM.”

### 4.5 Prospective feedback test: improvement with incomplete pitch coverage

Both supplementary runs succeeded without recorded errors: 77 commands and 24 movements for calibration, and 149 commands and 48 movements for the held-out comparison. Movement counts include positioning; only 12 and 24 strokes, respectively, were measurement trials. All 72 movements used the planned endpoints and Z=189.27 mm. Thus, the supplement adds a next-day observation, not an independent robot or a replicated agent-development session.

The calibration detector accepted 11/12 candidates and marked one uncertain. Four accepted candidates were octave-shifted relative to the expected injected-error relation: one upward and three downward. All candidates were retained, and the prescribed median yielded `k_fit = 4.98346880007365 Hz/(mm/s)`. The agent's recorded decision acknowledged these octave issues and proceeded with the frozen rule; no candidate was manually relabeled. Agreement with the earlier coefficient is supporting consistency, not an externally calibrated frequency standard.

**Table 5. Held-out feedback comparison. Each condition scheduled 12 strokes; uncertain estimates remain in the primary denominator.**

| Condition | Accepted estimates | Uncertain | Within ±25 cents | Median absolute error, accepted only |
|---|---:|---:|---:|---:|
| Frozen mapping with injected 8% scale error | 4/12 | 8/12 | 0/12 | 1066.83 cents |
| Measurement-based fitted mapping | 8/12 | 4/12 | 8/12 | 0.37 cents |

For the fitted mapping, pass counts were D4: 1/4, F4: 4/4, and A4: 3/4; both movement directions yielded 4/6 passes. The four uncertain cases comprised two competing-candidate decisions and two insufficient-harmonic decisions. Accepted fitted estimates ranged from −8.13 to +0.31 cents relative to their targets. The fixed-mapping arm had three upward-octave and one downward-octave candidate, explaining its large conditional median; that number is not the size of the injected scale error. Its other eight strokes had insufficient harmonic evidence. Full results, including failed and uncertain cases, are retained in [11].

The observed primary-endpoint difference was 8/12 versus 0/12 (66.7 percentage points), with no significance or population-effect claim. The sub-cent conditional median must not be read as sub-cent accuracy across all twelve notes or as a human listening result. The outcomes support feedback recovery in this constructed challenge while showing substantial dependence on note and detector coverage. They do not establish AI superiority: the update was conventional numerical fitting, and the agent had access to the prior project knowledge.

## 5 Discussion

### 5.1 Coupling between pitch range and travel

Higher-frequency targets required higher speeds, while the fixed 80 mm stroke shortened nominal movement duration as speed increased. For A6, the nominal stroke lasted approximately 80/353.148=0.227 s, but qualifying spectral-window centers covered only about 0.1 s. Reaching a high-note condition and sustaining it are therefore not interchangeable. The observations are consistent with acceleration constraints in bounded travel, but velocity trajectories were not independently measured; B6 failure cannot be attributed entirely to acceleration.

Increasing travel, using another axis, or changing the control method might change the outcome, but none was tested here. The manufacturer's 400 mm/s reliability statement also does not establish a reliable musical upper limit near 2 kHz.

### 5.2 Harmonics, octave ambiguity, and pitch accuracy

Motor motion produced multiple speed-dependent components, with low-register fundamentals potentially weaker than higher harmonics. The harmonic model supports relative frequency organization, but perception may involve octave substitution, additional pitches, or a pronounced mechanical timbre. Target-conditioned detection also introduces prior-selection bias. C1–A6 should consequently be interpreted as repeated spectral structures consistent with the tested targets, not a demonstrated range of clear pure tones.

Decimal places in the tables support parameter reproduction and arithmetic checks. An uncalibrated sampling clock, limited signal-to-noise ratio, finite FFT windows, and peak interpolation all affect absolute-frequency interpretation. Numerical precision should not be equated with acoustic measurement accuracy.

### 5.3 From command throughput to musical tempo

Some template errors were already present around 4–5 notes/s, whereas all notes matched in the 250 ms condition at approximately 2.9 notes/s. Future arrangements can therefore use about 3 notes/s as a more conservative tested operating point and treat about 4–5 notes/s as a marginal region requiring listening validation, rather than a guarantee.

The experiment used only three notes, fixed four-note phrases, and reversals every four notes. Short-note spectra may depend jointly on pitch, acceleration, deceleration, and direction changes. No randomized factorial experiment was performed to separate these effects. The observed classification performance cannot be transferred directly to a full scale, other registers, repeated identical notes, or different articulation gaps.

### 5.4 Limitations and further experiments

The original range/rhythm dataset used one robot in two experiments on the same day. The feedback supplement adds two next-day runs on that same robot, with a different note set and task; it is not a cross-day replication of the original range/rhythm design. Upper-register conditions generally had four strokes each, and fast-note conditions had sixteen notes each. Observations were dependent, without cross-day replication. Refinement conditions were selected from the initial results and therefore provide exploratory evidence. Microphone placement was not quantified. There was no formal blind listening test, external position or velocity measurement, sound-pressure calibration, or long-term durability evaluation.

Beyond the small held-out supplement, a generalizable usable range would require semitone-by-semitone sweeps with fixed microphone placement, multiple devices and dates, recorded velocity trajectories, and predefined persistence requirements. Perceptually distinguishable tempo should be assessed with balanced randomized note sequences, independent training and test recordings, fundamental-frequency estimation without target cues, and blind listening. These broader validations were not completed in this study.

### 5.5 What the case establishes about AI, and what remains to test

The observed contribution of the agent is orchestration and interpretation across tools: it implemented experiments, connected numerical acoustic evidence to protocol revisions, and produced executable artifacts under human-specified constraints. The case makes those decisions inspectable. It does not establish that an LLM is necessary for the speed–frequency fit, that it outperforms conventional optimization, or that it reduced human labor. No agent ablation, independent restart, intervention count, inference-cost log, or wall-clock comparison was collected prospectively. The documented human suggestions prevent treating the final architecture as an unaided discovery.

A prospective evaluation should compare three conditions with the same initial information, measurement tools, motion bounds, and robot-trial budget: a frozen mapping without feedback; a predefined numerical calibration method using feedback; and an agent that uses feedback to select tests and revise the mapping or arrangement. This comparison is proposed work, not an experiment reported here. The conventional feedback condition is essential for separating the value of measurement from any additional value of AI reasoning.

Before collecting data, the evaluator should freeze acceptance thresholds, stopping rules, and an independent scoring method. Balanced randomized note sequences and separately recorded held-out targets should assess pitch error, octave mistakes, acoustic onset error, and task completion. Ambiguous fundamentals should be scored as uncertain rather than assigned to the expected note. Record physical trial counts, elapsed time, compute cost, and the source and timing of human interventions. Repeat from reset initial conditions across dates; additional devices would test transfer rather than being assumed equivalent. An agent that helps author a detector must not be allowed to revise the held-out scoring rule after seeing its test results.

## 6 Conclusion

This case documents human–AI co-development of motor music through an experiment-level acoustic feedback loop. The operator set goals and physical constraints and introduced key motion-design ideas; the agent implemented experiments and interpreted tool-generated measurements; deterministic code compiled and checked the motion executed by the robot. Recorded calibration and refinement episodes show that physical observations changed later actions. They do not demonstrate an autonomous real-time pitch controller or a causal advantage over conventional calibration.

The supporting single-device experiments show why acoustic validation matters: repeated harmonic evidence covered discrete C1–A6 targets, yet low-register ambiguity and short high-register persistence constrained interpretation. Approximately 4–5 notes/s already showed identification losses. The next-day held-out supplement improved the predefined pitch endpoint from 0/12 to 8/12 after numerical feedback, with four uncertain outcomes. The resulting contribution is a documented architecture and bounded empirical case; the incremental value of AI over a conventional feedback method remains to be tested.

## Data, code, and reproducibility

The repository contains the two executed protocols, offline analysis code, a reviewed compact result dataset at `docs/research/data/evidence.json`, and figure/report build scripts. The dataset retains per-note command times, template predictions, qualifying harmonics for individual movements, and SHA-256 hashes of original source files. Figures can be rebuilt from this dataset alone; spectral re-extraction additionally requires the original local WAV files and execution records.

Reviewed Chinese and English article PDFs are distributed in `docs/research/pdf/`. Original recordings, individual HTTP logs, runtime environments, and intermediate build products remain in Git-ignored local directories. Audio is not an open dataset. File hashes support later verification but do not make the missing source data downloadable. The absence of original audio limits independent external reanalysis, and the report does not claim complete open-data reproducibility.

The experiments are labeled “Initial” and “Refinement.” Actual device, protocol, analysis, and execution identifiers are excluded from the publication. Detailed methods and results are recorded in [6]. Dates follow the control computer, with robot clock differences handled as described above.

The supplementary runner, frozen scoring code, and reviewed `docs/research/data/feedback-evidence.json` support the next-day results [11]. Its two recordings, source hashes, fit decision, and every scheduled trial are documented without publishing raw transport records.

The workflow and human-role supplement [10] distinguishes conversational attribution from recorded execution evidence. It publishes paraphrased decisions without device identifiers, local network configuration, or execution identifiers.

## Human contributions and AI-use disclosure

The operator's contributions include problem formulation, physical setup, operating constraints, phrase-level planning and precomposition suggestions, research framing, and requests for dissemination. The coding agent assisted literature lookup, software implementation, experimental orchestration, analysis interpretation, and manuscript preparation. Numerical audio analysis and motion compilation were performed by deterministic software. These statements describe activities; they do not assign formal authorship to an AI tool.

An exact model snapshot, inference configuration, complete prompt/tool trace, intervention inventory, and token/cost record for the experimental session were not preserved in the publication package. The agent used to revise this manuscript must not be assumed to identify the model used for every earlier experiment. This limits reproduction of agent behavior and model-specific comparisons. The role/decision supplement [10] is a curated retrospective account, not a replacement for a complete execution trace.

The author name and correspondence were supplied by the operator. Affiliation, funding, and competing-interest declarations remain to be supplied by the author before submission. Human authors must review and take responsibility for the complete manuscript, including AI-assisted content. This draft has not been submitted to arXiv or a journal and has not undergone peer review.

## References

1. nescio007. *midi2gcode: A MIDI to G-code converter*. Open-source software repository. https://github.com/nescio007/midi2gcode (accessed 14 September 2026).
2. Toglefritz. *Musical Marlin: Make your 3D printer play music*. Open-source software repository. https://github.com/Toglefritz/Musical_Marlin (accessed 14 September 2026).
3. Opentrons. *Python API: Labware and Deck Positions — Gantry Speed*. Official technical documentation. https://docs.opentrons.com/python-api/robot-position/#gantry-speed (accessed 14 September 2026).
4. Opentrons AI project records. [OT-2 motor-pitch calibration and Song of Storms listening samples](../ot2-pitch-calibration-results.md). 14 September 2026. Project technical record in Chinese; not peer reviewed.
5. Opentrons AI project records. [Complete motor music arrangements](../ot2-music-full-arrangements.md). 14 September 2026. Project technical record.
6. Opentrons AI project records. [OT-2 pitch-range and rhythm measurements](../ot2-music-limits.md). 14 September 2026. Project record in Chinese, including criteria and anonymized execution results.
7. Long, J., Kapur, A., and Carnegie, D. A. *The Closed-Loop Robotic Glockenspiel: Improving Musical Robots Using Embedded Musical Information Retrieval*. Proceedings of NIME, 2016, pp. 2–7. [Conference paper](https://www.nime.org/proceedings/2016/nime2016_paper0002.pdf).
8. Huang, W., et al. *Inner Monologue: Embodied Reasoning through Planning with Language Models*. 2022. [arXiv:2207.05608](https://arxiv.org/abs/2207.05608).
9. Bhat, V., Kaypak, A. U., Krishnamurthy, P., Karri, R., and Khorrami, F. *Grounding LLMs For Robot Task Planning Using Closed-loop State Feedback*. 2024; revised 2025. [arXiv:2402.08546](https://arxiv.org/abs/2402.08546).
10. Opentrons AI project. [Human–AI workflow evidence and attribution](https://github.com/chenmzh/opentrons-ai/blob/main/docs/research/workflow-evidence.md). Curated retrospective supplement, 15 September 2026; based on operator instructions, technical records, and source inspection.
11. Opentrons AI project. [Prospective acoustic-feedback validation](https://github.com/chenmzh/opentrons-ai/blob/main/docs/research/feedback-validation.md). 15 September 2026. Includes the frozen plan, numerical evidence, and execution outcome.
