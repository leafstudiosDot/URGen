from __future__ import annotations

import argparse
import json
from pathlib import Path

from core.config import PipelineConfig
from core.orchestrator import Orchestrator


def _parse_args() -> argparse.Namespace:
	parser = argparse.ArgumentParser(description="URGen pipeline runner.")
	parser.add_argument("topic", help="Topic for the short story.")
	parser.add_argument(
		"--model",
		default="qwen3.5:2b",
		choices=["mistral", "gpt-oss:120b-cloud", "deepseek-r1", "qwen3.5"],
	)
	parser.add_argument("--voice", default="julie", choices=["julie", "daniel"])
	parser.add_argument("--background", default=None)
	parser.add_argument("--output-dir", default="output")
	parser.add_argument("--width", type=int, default=1080)
	parser.add_argument("--height", type=int, default=1920)
	parser.add_argument("--fps", type=int, default=60)
	parser.add_argument("--font-size", type=int, default=14)
	parser.add_argument(
		"--upload",
		default="",
		help="Comma-separated platforms to upload to after render (youtube,tiktok).",
	)
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

	if args.upload:
		platforms = [p.strip().lower() for p in args.upload.split(",") if p.strip()]
		metadata = {}
		try:
			metadata = json.loads(result.metadata_path.read_text(encoding="utf-8"))
		except Exception:
			metadata = {}
		title = metadata.get("title") or args.topic
		description = metadata.get("description") or args.topic
		tags = metadata.get("tags") or [args.topic]
		hashtags = metadata.get("hashtags") or []
		if hashtags:
			description = description + "\n\n" + " ".join(hashtags)
		yt_privacy = metadata.get("youtube_privacy") or "public"
		tt_privacy = metadata.get("tiktok_privacy") or "PUBLIC_TO_EVERYONE"
		tiktok_title = title
		if hashtags:
			tiktok_title = (title + " " + " ".join(hashtags))[:150]

		if "youtube" in platforms:
			try:
				from upload.youtube import upload_video as yt_upload

				yt_upload(
					result.video_path,
					title=title,
					description=description,
					tags=tags,
					privacy_status=yt_privacy,
				)
			except Exception as exc:
				print(f"[upload] YouTube failed: {exc}")
		if "tiktok" in platforms:
			try:
				from upload.tiktok import upload_video as tt_upload

				tt_upload(
					result.video_path,
					title=tiktok_title,
					privacy_level=tt_privacy,
				)
			except Exception as exc:
				print(f"[upload] TikTok failed: {exc}")

	return 0


if __name__ == "__main__":
	raise SystemExit(main())
