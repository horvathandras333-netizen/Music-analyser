import argparse
import sys
from pathlib import Path
from typing import Literal

from analysis.grid import analyze_track
from report.render import render_report
from spec.builder import build_clip_spec
from spec.candidates import enumerate_candidates


def main(args_list: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="loopforge",
        description="LoopForge — Audio tempo & beat grid analysis for loop-safe video clip specs.",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    analyze_parser = subparsers.add_parser("analyze", help="Analyze audio file and print clip spec report")
    analyze_parser.add_argument("path", type=str, help="Path to audio file (WAV, MP3, FLAC)")
    analyze_parser.add_argument("--target", type=float, default=10.0, help="Target clip duration in seconds (default: 10.0)")
    analyze_parser.add_argument("--fps", type=int, default=24, help="Target video frame rate (default: 24)")
    analyze_parser.add_argument("--start", type=float, default=None, help="Clip start time in seconds")
    analyze_parser.add_argument("--end", type=float, default=None, help="Clip end time in seconds")
    analyze_parser.add_argument(
        "--loop-mode",
        type=str,
        choices=["ping_pong", "true_cycle"],
        default="ping_pong",
        help="Loop mode preference (default: ping_pong)",
    )

    parsed_args = parser.parse_args(args_list if args_list is not None else sys.argv[1:])

    if not parsed_args.command:
        parser.print_help()
        return 1

    if parsed_args.command == "analyze":
        file_path = Path(parsed_args.path)
        analysis = analyze_track(file_path)

        candidates = enumerate_candidates(
            analysis.bpm, target_duration_s=parsed_args.target, meter=analysis.meter
        )
        if parsed_args.start is not None and parsed_args.end is not None:
            start_s = float(parsed_args.start)
            end_s = float(parsed_args.end)
        else:
            top_duration = candidates[0][2] if candidates else parsed_args.target

            start_s = float(parsed_args.start) if parsed_args.start is not None else (
                analysis.downbeat_times[0] if analysis.downbeat_times else 0.0
            )
            if parsed_args.end is not None:
                end_s = float(parsed_args.end)
            else:
                end_s = start_s + top_duration

        loop_mode_val: Literal["ping_pong", "true_cycle"] = parsed_args.loop_mode
        spec = build_clip_spec(
            start_s=start_s,
            end_s=end_s,
            bpm=analysis.bpm,
            fps=parsed_args.fps,
            meter=analysis.meter,
            loop_mode=loop_mode_val,
            downbeat_times=analysis.downbeat_times,
        )

        report_text = render_report(analysis, spec, candidates=candidates)
        print(report_text)
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
