from __future__ import annotations

import argparse
from pathlib import Path

from seminar_compass.models import InputType, ReconstructionRequest
from seminar_compass.pipeline import SeminarCompassPipeline
from seminar_compass.view import render_result_view


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seminar Compass MVP raw-text entrypoint")
    parser.add_argument(
        "--text",
        help="Raw text content to reconstruct.",
    )
    parser.add_argument(
        "--text-file",
        help="Path to a UTF-8 text file containing raw text content.",
    )
    parser.add_argument(
        "--support-file",
        action="append",
        default=[],
        help="Optional support material text file. Can be passed multiple times.",
    )
    parser.add_argument(
        "--mode",
        default="base",
        choices=["base", "preview", "review", "easier"],
        help="Which output_type view to render.",
    )
    return parser.parse_args()


def _read_text(args: argparse.Namespace) -> str:
    if args.text:
        return args.text.strip()
    if args.text_file:
        return Path(args.text_file).read_text(encoding="utf-8").strip()
    raise ValueError("Provide --text or --text-file.")


def main() -> int:
    args = _parse_args()
    try:
        primary_text = _read_text(args)
    except ValueError as exc:
        print(str(exc))
        return 2

    support_materials = [Path(p).read_text(encoding="utf-8").strip() for p in args.support_file]

    pipeline = SeminarCompassPipeline()
    response = pipeline.reconstruct(
        ReconstructionRequest(
            input_type=InputType.RAW_TEXT,
            content=primary_text,
            support_materials=support_materials,
        )
    )

    selected = next((o for o in response.primary_outputs if o.output_type.value == args.mode), None)
    if selected is None:
        print(f"Requested mode '{args.mode}' not available.")
        return 2

    print(render_result_view(selected))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
