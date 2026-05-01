from __future__ import annotations

from pathlib import Path

def _escape_subtitles_path(path: Path) -> str:
	posix_path = path.resolve().as_posix()
	return posix_path.replace(":", "\\:")

def build_ffmpeg_command(
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
) -> list[str]:
	command: list[str] = ["ffmpeg", "-y"]

	if background_list_path is not None:
		command += ["-f", "concat", "-safe", "0", "-i", str(background_list_path)]
	elif background_path is None:
		command += [
			"-f",
			"lavfi",
			"-i",
			f"color=c=black:s={width}x{height}:r={fps}",
		]
	else:
		command += ["-stream_loop", "-1", "-i", str(background_path)]

	command += ["-i", str(audio_path)]
	if music_path is not None:
		command += ["-i", str(music_path)]

	video_filters = [f"scale={width}:{height}"]
	if subtitles_path is not None:
		subtitle_filter = (
			"subtitles='"
			+ _escape_subtitles_path(subtitles_path)
			+ f"':force_style='Fontsize={font_size},PrimaryColour=&H{_bgr_color(font_color)},"
			f"OutlineColour=&H{_bgr_color(font_border_color)},Outline={font_border_size},"
			"Alignment=5'"
		)
		video_filters.append(subtitle_filter)

	audio_filters: list[str] = []
	if music_path is not None:
		audio_filters.append("[1:a]volume=1.0[a1]")
		audio_filters.append(f"[2:a]volume={music_volume}[a2]")
		audio_filters.append(
			"[a1][a2]amix=inputs=2:duration=shortest:dropout_transition=2[aout]"
		)
	else:
		audio_filters.append("[1:a]anull[aout]")

	filter_complex = ";".join(audio_filters)

	command += [
		"-vf",
		",".join(video_filters),
		"-filter_complex",
		filter_complex,
		"-map",
		"0:v",
		"-map",
		"[aout]",
		"-t",
		f"{max(audio_duration, 0.1):.3f}",
		"-shortest",
		"-c:v",
		"libx264",
		"-pix_fmt",
		"yuv420p",
		"-c:a",
		"aac",
		"-b:a",
		"192k",
		"-r",
		str(fps),
		str(output_path),
	]
	return command

def _bgr_color(color: str) -> str:
	normalized = color.strip().lower()
	named = {
		"white": "FFFFFF",
		"black": "000000",
		"yellow": "00FFFF",
	}
	hex_color = named.get(normalized, normalized.lstrip("#"))
	hex_color = hex_color.zfill(6)
	return f"{hex_color[4:6]}{hex_color[2:4]}{hex_color[0:2]}"
