from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class PipelineConfig:
	output_dir: Path = Path("output")
	raw_audio_dir: Path = field(default_factory=lambda: Path("output") / "raw_audio")
	raw_video_dir: Path = field(default_factory=lambda: Path("output") / "raw_video")
	final_dir: Path = field(default_factory=lambda: Path("output") / "final_shorts")
	assets_dir: Path = Path("assets")
	backgrounds_dir: Path = field(default_factory=lambda: Path("assets") / "backgrounds")
	music_dir: Path = field(default_factory=lambda: Path("assets") / "music")
	background_path: Path | None = None
	model: str = "mistral"
	voice: str = "julie"
	whisper_model: str = "base"
	width: int = 1080
	height: int = 1920
	fps: int = 60
	font_size: int = 24
	font_color: str = "white"
	font_border_color: str = "black"
	font_border_size: int = 2
	music_volume: float = 0.25
