from __future__ import annotations

import argparse
from pathlib import Path

from core.config import PipelineConfig
from core.orchestrator import Orchestrator

def _parse_args() -> argparse.Namespace:
	parser = argparse.ArgumentParser(description="URGen pipeline runner.")
	parser.add_argument("topic", help="Topic for the short story.")
	parser.add_argument("--model", default="mistral")
	parser.add_argument("--voice", default="julie", choices=["julie", "daniel"])
	parser.add_argument("--background", default=None)
	parser.add_argument("--output-dir", default="output")
	parser.add_argument("--width", type=int, default=1080)
	parser.add_argument("--height", type=int, default=1920)
	parser.add_argument("--fps", type=int, default=60)
	parser.add_argument("--font-size", type=int, default=14)
	return parser.parse_args()

def main() -> int:
	args = _parse_args()
	output_dir = Path(args.output_dir)
	config = PipelineConfig(
		output_dir=output_dir,
		raw_audio_dir=output_dir / "raw_audio",
		raw_video_dir=output_dir / "raw_video",
		final_dir=output_dir / "final_shorts",
		background_path=Path(args.background) if args.background else None,
		assets_dir=Path("assets"),
		backgrounds_dir=Path("assets") / "backgrounds",
		music_dir=Path("assets") / "music",
		model=args.model,
		voice=args.voice,
		width=args.width,
		height=args.height,
		fps=args.fps,
		font_size=args.font_size,
	)

	orchestrator = Orchestrator(config)
	result = orchestrator.run(args.topic)
	print(str(result.video_path))
	return 0

if __name__ == "__main__":
	raise SystemExit(main())
