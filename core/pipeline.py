from __future__ import annotations

from dataclasses import dataclass
import random
import subprocess
from pathlib import Path

from core.config import PipelineConfig
from scripts.script_generator import generate_script
from subtitles.subtitle_builder import write_srt
from subtitles.whisper_engine import transcribe
from tts.oddcast import generate_mp3
from video.video_editor import render_video

@dataclass
class PipelineResult:
	script_path: Path
	audio_path: Path
	subtitles_path: Path
	video_path: Path

def run_pipeline(topic: str, config: PipelineConfig) -> PipelineResult:
	config.raw_audio_dir.mkdir(parents=True, exist_ok=True)
	config.raw_video_dir.mkdir(parents=True, exist_ok=True)
	config.final_dir.mkdir(parents=True, exist_ok=True)

	script_text = generate_script(topic, model=config.model)
	script_path = config.raw_audio_dir / f"{_slugify(topic)}.txt"
	script_path.write_text(script_text, encoding="utf-8")

	audio_path = generate_mp3(
		script_text,
		config.raw_audio_dir,
		voice=config.voice,
	)

	music_path = _pick_random_file(config.music_dir, (".mp3",))
	background_path = config.background_path
	background_list_path: Path | None = None
	if background_path is None:
		backgrounds = _list_media_files(config.backgrounds_dir, (".mp4",))
		if backgrounds:
			background_list_path = _build_background_playlist(
				backgrounds,
				audio_path,
				config.raw_video_dir,
			)
		else:
			background_path = None

	audio_duration = _get_media_duration_seconds(audio_path)
	segments = transcribe(str(audio_path))
	subtitles_path = config.raw_video_dir / f"{_slugify(topic)}.srt"
	write_srt(segments, subtitles_path)

	video_path = config.final_dir / f"{_slugify(topic)}.mp4"
	render_video(
		background_path=background_path,
		background_list_path=background_list_path,
		audio_path=audio_path,
		music_path=music_path,
		subtitles_path=subtitles_path,
		output_path=video_path,
		audio_duration=audio_duration,
		width=config.width,
		height=config.height,
		fps=config.fps,
		font_size=config.font_size,
		font_color=config.font_color,
		font_border_color=config.font_border_color,
		font_border_size=config.font_border_size,
		music_volume=config.music_volume,
	)

	return PipelineResult(
		script_path=script_path,
		audio_path=audio_path,
		subtitles_path=subtitles_path,
		video_path=video_path,
	)

def _slugify(text: str) -> str:
	cleaned = "".join(c for c in text if c.isalnum() or c in " -_").strip()
	return "-".join(cleaned.split()).lower() or "urgen"

def _list_media_files(directory: Path, extensions: tuple[str, ...]) -> list[Path]:
	if not directory.exists():
		return []
	return [path for path in directory.iterdir() if path.suffix.lower() in extensions]

def _pick_random_file(directory: Path, extensions: tuple[str, ...]) -> Path | None:
	files = _list_media_files(directory, extensions)
	return random.choice(files) if files else None

def _build_background_playlist(
	backgrounds: list[Path],
	audio_path: Path,
	output_dir: Path,
) -> Path:
	audio_duration = _get_media_duration_seconds(audio_path)
	playlist: list[Path] = []
	current = 0.0
	while current < audio_duration:
		choice = random.choice(backgrounds)
		playlist.append(choice)
		current += max(_get_media_duration_seconds(choice), 1.0)

	output_dir.mkdir(parents=True, exist_ok=True)
	playlist_path = output_dir / f"backgrounds_{audio_path.stem}.txt"
	lines = [f"file '{path.resolve().as_posix()}'" for path in playlist]
	playlist_path.write_text("\n".join(lines), encoding="utf-8")
	return playlist_path

def _get_media_duration_seconds(path: Path) -> float:
	try:
		result = subprocess.run(
			[
				"ffprobe",
				"-v",
				"error",
				"-show_entries",
				"format=duration",
				"-of",
				"default=noprint_wrappers=1:nokey=1",
				str(path),
			],
			check=True,
			capture_output=True,
			text=True,
		)
		value = result.stdout.strip()
		return float(value) if value else 0.0
	except (subprocess.SubprocessError, ValueError):
		return 0.0