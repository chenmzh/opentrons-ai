"""Happy Birthday：完整庆生编排 — precomposed, bounded phrase motion.

Run on the host: python3 protocols/ot2_happy_birthday.py
No tips; fixed post-home Z; 5 mm inset within the tested 100 mm X interval.
Whole score/path are computed before home; reversals occur only at phrase edges.
The embedded planner keeps this file independently uploadable as an OT-2 protocol.
Source melody: https://www.musicallthetime.com/happy-birthday-sheet-music.html
Robot-side move_to remains segment-based, not continuous firmware buffering.
"""

import itertools
import math

metadata = {
    "protocolName": "OT-2 happy-birthday: precomposed full arrangement",
    "description": "Complete score; phrase-boundary reversals; fixed Z; 5 mm inset.",
}
requirements = {"robotType": "OT-2", "apiLevel": "2.22"}

CENTER_X_MM = 196.5
CENTER_Y_MM = 178.75
MIN_X_MM = 146.5
MAX_X_MM = 246.5
MARGIN_MM = 5.0
HZ_PER_MM_S = 4.98375
TEMPO_QUARTER_BPM = 96.0
MAX_SPEED_MM_S = 30.0
MIDI = {"G1": 31, "A1": 33, "B1": 35, "C2": 36, "D2": 38,
        "E2": 40, "F2": 41, "G2": 43}
PHRASES = (
    (("G1", .75), ("G1", .25), ("A1", 1), ("G1", 1), ("C2", 1), ("B1", 2)),
    (("G1", .75), ("G1", .25), ("A1", 1), ("G1", 1), ("D2", 1), ("C2", 2)),
    (("G1", .75), ("G1", .25), ("G2", 1), ("E2", 1), ("C2", 1), ("B1", 1), ("A1", 1)),
    (("F2", .75), ("F2", .25), ("E2", 1), ("C2", 1), ("D2", 1), ("C2", 2)),
)
# Original motor arrangement: intro, theme, interlude, theme twice, final cadence.
INTRO = (("C2", 1), ("E2", 1), ("G2", 1), ("E2", 1), ("C2", 2))
INTERLUDE = (("C2", 1), ("E2", 1), ("G2", 1), ("F2", 1), ("E2", 1), ("D2", 1))
CODA = (("F2", 1), ("E2", 1), ("D2", 1), ("G1", 1), ("C2", 2))


def score_phrases():
    return (INTRO,) + PHRASES + (INTERLUDE,) + PHRASES * 2 + (CODA,)


def choose_phrase_path(distances_mm):
    """Search whole-phrase directions, minimizing reversals then occupied span.

    Translate the resulting path to center its extrema in the inset envelope.
    A phrase is monotonic, so its endpoints bound every note within it.
    """
    width_mm = MAX_X_MM - MIN_X_MM - 2 * MARGIN_MM
    if not 1 <= len(distances_mm) <= 16:
        raise ValueError("Phrase-direction search requires 1–16 phrases")
    if any(not math.isfinite(d) or not 0 < d <= width_mm for d in distances_mm):
        raise ValueError("A whole phrase exceeds the inset travel range; revise tempo or register")
    best = None
    # Mirrored paths are equivalent; prefer the first phrase moving toward +X.
    for tail in itertools.product((1, -1), repeat=len(distances_mm) - 1):
        directions = (1, *tail)
        points = [0.0]
        for index, direction in enumerate(directions):
            points.append(points[-1] + direction * distances_mm[index])
        span = max(points) - min(points)
        if span > width_mm:
            continue
        reversals = sum(directions[i - 1] != directions[i] for i in range(1, len(directions)))
        score = (reversals, span)
        if best is None or score < best[0]:
            start_x_mm = CENTER_X_MM - (min(points) + max(points)) / 2
            best = (score, start_x_mm, directions)
    if best is None:
        raise ValueError("No whole-phrase route fits; revise the arrangement before execution")
    return best[1], best[2]

def compose(tempo_bpm=TEMPO_QUARTER_BPM, phrases=None):
    if not math.isfinite(tempo_bpm) or tempo_bpm <= 0:
        raise ValueError("Tempo must be finite and positive")
    score = score_phrases() if phrases is None else phrases
    phrases = []
    for phrase_index, phrase in enumerate(score, 1):
        if not phrase or any(not math.isfinite(beats) or beats <= 0 for _, beats in phrase):
            raise ValueError("Phrases must contain notes with finite positive durations")
        events = []
        for index, (name, beats) in enumerate(phrase):
            hz = 440.0 * 2.0 ** ((MIDI[name] - 69) / 12.0)
            speed_mm_s = hz / HZ_PER_MM_S
            duration_s = beats * 60.0 / tempo_bpm
            # These rests belong to the note duration, rather than extending it.
            # Articulate repeated pickup notes; breathe only at phrase ends.
            gap_s = .08 if index == len(phrase) - 1 else (
                .04 if phrase[index + 1][0] == name else 0.0)
            tone_s = duration_s - gap_s
            if not (0 < speed_mm_s <= MAX_SPEED_MM_S and tone_s > 0):
                raise ValueError("Note duration or speed is outside the motion envelope")
            events.append(dict(phrase=phrase_index, note=name, hz=hz, duration_s=duration_s,
                               tone_s=tone_s, gap_after_s=gap_s, speed_mm_s=speed_mm_s,
                               distance_mm=speed_mm_s * tone_s))
        phrases.append(events)
    distances = [sum(e["distance_mm"] for e in phrase) for phrase in phrases]
    start_x_mm, directions = choose_phrase_path(distances)
    x_mm = start_x_mm
    notes = []
    for phrase_index, phrase in enumerate(phrases):
        direction = directions[phrase_index]
        for event in phrase:
            x_mm += direction * event["distance_mm"]
            if not MIN_X_MM + MARGIN_MM <= x_mm <= MAX_X_MM - MARGIN_MM:
                raise ValueError("A composed note violates the 5 mm inset")
            notes.append(dict(event, x_mm=x_mm, direction=direction))
    return dict(start_x_mm=start_x_mm, directions=directions,
                phrase_distances_mm=distances, notes=notes)

def run(protocol):
    from opentrons import types
    from opentrons.protocol_engine.commands import SavePositionParams

    arrangement = compose()
    pipette = protocol.load_instrument("p300_multi_gen2", "left")
    protocol.home()
    core = pipette._core

    def position():
        return core._engine_client.execute_command_without_recovery(
            SavePositionParams(pipetteId=core._pipette_id, failOnNotHomed=True),
            command_annotations=[],
        ).position

    home = position()
    z_mm = 200.0 if protocol.is_simulating() else home.z
    if not math.isfinite(z_mm) or z_mm < 150:
        raise RuntimeError(f"Unexpected home height: {z_mm} mm")

    def move(x_mm, speed_mm_s):
        if not (MIN_X_MM + MARGIN_MM <= x_mm <= MAX_X_MM - MARGIN_MM
                and 0 < speed_mm_s <= MAX_SPEED_MM_S):
            raise RuntimeError("Move violates the inset travel range or speed limit")
        pipette.move_to(types.Location(types.Point(x_mm, CENTER_Y_MM, z_mm), None),
                        force_direct=True, speed=speed_mm_s)

    move(arrangement["start_x_mm"], 30.0)
    protocol.comment(f"MUSIC_BASELINE Z={z_mm:.5f} mm")
    protocol.delay(seconds=3)
    protocol.comment("HAPPY_BIRTHDAY_BEGIN")
    previous_phrase = None
    for event in arrangement["notes"]:
        if event["phrase"] != previous_phrase:
            protocol.comment(f"PHRASE {event['phrase']} direction={event['direction']}")
            previous_phrase = event["phrase"]
        move(event["x_mm"], event["speed_mm_s"])
        if event["gap_after_s"]:
            protocol.delay(seconds=event["gap_after_s"])
    protocol.comment("HAPPY_BIRTHDAY_END")
    final = position()
    if not protocol.is_simulating() and (
            not math.isfinite(final.z) or abs(final.z - z_mm) > .05):
        raise RuntimeError("Z changed during playback")
    protocol.comment(f"MUSIC_COMPLETE Z={final.z:.5f} mm")

if __name__ == "__main__":
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
    from opentrons_ai.music_runner import main

    arrangement = compose()
    print("乐句方向：", arrangement["directions"], flush=True)
    raise SystemExit(main(Path(__file__).resolve(), arrangement["notes"],
                          title="Happy Birthday：完整庆生编排", slug="happy-birthday",
                          start_x_mm=arrangement["start_x_mm"], max_speed_mm_s=MAX_SPEED_MM_S))
