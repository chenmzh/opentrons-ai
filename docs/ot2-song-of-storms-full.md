# Song of Storms: complete motor melody

The current script has been upgraded to full-score phrase planning. See
[the current arrangements and Python commands](ot2-music-full-arrangements.md)
for the revised structure, boundaries, and validation.

## Historical version before the full-arrangement update

The remainder of this page records the earlier source and its results.
The current protocol file differs; old protocol/run IDs refer to that earlier
version. Exact uploaded copies remain in their recorded run directories.

Completed on 2026-09-14: the physical run returned `succeeded`, with all 183
commands successful and no run errors. The 86-note performance took 50.77
seconds, excluding homing, approach, and cleanup. Initial and final saved
position readings both reported Z=189.27000 mm; every commanded music move
used Z=189.27 mm.

Listen to the [complete performance](../runs/music/session-20260914/song-full/full-song-listen.wav).
The [raw clip](../runs/music/session-20260914/song-full/full-song.wav) and
[full recording](../runs/music/session-20260914/song-full/recording.wav) are also
retained. The listening copy removes constant DC and applies +11.44 dB uniform
gain, without pitch or rhythm changes. No samples clipped in the raw music clip.

The user accepted the low-register relative-pitch calibration and authorized
the complete piece. The standalone script is
[ot2_song_of_storms_full.py](../protocols/ot2_song_of_storms_full.py).

This monophonic arrangement includes all 15 melody bars, played twice, ending
on D2: 86 note strokes. It follows
[DoubleMark's concert-pitch transcription at VGLeadSheets](https://www.vgleadsheets.com/assets/sheets/C/The%20Legend%20of%20Zelda%20-%20Ocarina%20of%20Time%20-%20Song%20of%20Storms.pdf),
lowered two octaves. Accompaniment-only introduction and turnaround bars are
omitted. Quarter-note tempo is 132 BPM; the nominal moving-note duration is
40.91 seconds. Acceleration and command overhead lengthen actual performance.

The previous X-axis harmonic-spacing calibration, 4.98375 Hz/(mm/s), is retained.
Notes span D2–F3 and use 14.731–35.037 mm/s. The highest notes extend beyond
the earlier six-note trial's 30 mm/s cap; the full script caps speed at 36 mm/s.
The model preserves note intervals but does not establish pure-tone timbre or
independently verify every short note's acoustic pitch.

Each note moves toward the center, preventing accumulated X drift. Actual
planned X endpoints span 168.561–222.650 mm, inside the previous 100 mm circle's
bounding box. Y stays 178.75 mm. After homing, the actual left-pipette height
is read and retained for every direct move. No labware, tips, aspiration, or
dispensing are used. The script checks final Z against its initial reading.

Offline tests cover score completeness, note intervals, movement duration,
bounded travel, fixed Z, and invalid-height handling. Robot-side simulation
completed with result `ok`, no errors, and 87 direct movement commands (one
approach plus 86 note strokes), all at simulated Z=200 mm.


The analyzed script was invoked with a local recording runner using the locally
returned protocol and analysis identifiers. Those identifiers are not published.

The runner checks current identity, pipettes, sessions, analysis, and run state
before sending `play` once. Host audio is recorded with PipeWire input 46,
16 kHz mono PCM, at the previously checked 0.35 input volume. Local run and
recording artifacts are ignored by Git.

Verification: seven offline music-protocol tests passed; Ruff on the new
protocol and tests, and `git diff --check`, passed. The precise motion, timing,
recording statistics, and run result are in the local
`song-full/performance-summary.json`, alongside command and HTTP logs.
