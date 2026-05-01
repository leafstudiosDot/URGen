from __future__ import annotations

import subprocess
from pathlib import Path

from video.ffmpeg_builder import build_ffmpeg_command

def render_video(
    *,
    background_path: Path | None,
	background_list_path: Path | None,
    audio_path: Path,
	music_path: Path | None,
    subtitles_path: Path | None,
    output_path: Path,
	audio_duration: float,
    width: int,
    height: int,
    fps: int,
    font_size: int,
    font_color: str,
    font_border_color: str,
    font_border_size: int,
	music_volume: float,
) -> None:
    command = build_ffmpeg_command(
        background_path=background_path,
		background_list_path=background_list_path,
        audio_path=audio_path,
		music_path=music_path,
        subtitles_path=subtitles_path,
        output_path=output_path,
		audio_duration=audio_duration,
        width=width,
        height=height,
        fps=fps,
        font_size=font_size,
        font_color=font_color,
        font_border_color=font_border_color,
        font_border_size=font_border_size,
		music_volume=music_volume,
    )
    subprocess.run(command, check=True)