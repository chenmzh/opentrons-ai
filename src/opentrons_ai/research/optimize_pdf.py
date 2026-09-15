"""Losslessly compact PDF streams after browser export; retain text and vectors."""

import argparse
from pathlib import Path


def main():
    import pikepdf

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.input.resolve() == args.output.resolve():
        parser.error("Use distinct input and output files")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    pikepdf.settings.set_flate_compression_level(9)
    with pikepdf.open(args.input) as pdf:
        pdf.remove_unreferenced_resources()
        pdf.save(
            args.output,
            object_stream_mode=pikepdf.ObjectStreamMode.generate,
            compress_streams=True,
            recompress_flate=True,
        )
    print(f"PDF: {args.output} ({args.output.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
