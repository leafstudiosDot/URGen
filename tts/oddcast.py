"""Oddcast TTS downloader.

Builds the Oddcast URL, downloads the MP3, and names it based on the TXT value.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from urllib.parse import quote, unquote, urlencode
from urllib.request import urlopen

ODDCAST_BASE_URL = "https://cache-a.oddcast.com/tts/genC.php"
VOICE_PRESETS = {
	"julie": {"eid": 3, "lid": 1, "vid": 3, "scene_id": 2770530},
	"daniel": {"eid": 4, "lid": 1, "vid": 5, "scene_id": 2770702},
}

def _sanitize_filename(name: str, max_len: int = 120) -> str:
	# Windows invalid characters: <>:"/\\|?* and control chars.
	sanitized = re.sub(r"[<>:\"/\\|?*\x00-\x1F]", "", name).strip()
	sanitized = re.sub(r"\s+", " ", sanitized)
	if not sanitized:
		sanitized = "oddcast_tts"
	return sanitized[:max_len]

def build_oddcast_url(
	*,
	text: str,
	eid: int,
	lid: int,
	vid: int,
	acc: int = 9066743,
	scene_id: int,
	ext: str = "mp3",
	fname: str = "",
	http_err: str = "",
	text_is_encoded: bool = False,
) -> str:
	encoded_text = text if text_is_encoded else quote(text, safe="")
	query = {
		"EID": eid,
		"LID": lid,
		"VID": vid,
		"TXT": encoded_text,
		"EXT": ext,
		"FNAME": fname,
		"ACC": acc,
		"SceneID": scene_id,
		"HTTP_ERR": http_err,
	}
	return f"{ODDCAST_BASE_URL}?{urlencode(query, quote_via=quote, safe='%')}"

def resolve_voice_params(
	*,
	voice: str = "julie",
	eid: int | None = None,
	lid: int | None = None,
	vid: int | None = None,
	scene_id: int | None = None,
) -> tuple[int, int, int, int]:
	voice_key = voice.lower().strip()
	if voice_key in VOICE_PRESETS:
		preset = VOICE_PRESETS[voice_key]
		eid = preset["eid"] if eid is None else eid
		lid = preset["lid"] if lid is None else lid
		vid = preset["vid"] if vid is None else vid
		scene_id = preset["scene_id"] if scene_id is None else scene_id
	if eid is None or lid is None or vid is None or scene_id is None:
		raise ValueError("EID, LID, VID, and SceneID are required.")
	return eid, lid, vid, scene_id

def download_mp3(url: str, output_path: Path) -> None:
	output_path.parent.mkdir(parents=True, exist_ok=True)
	print(f"[tts] Downloading MP3 -> {output_path}")
	with urlopen(url) as response, open(output_path, "wb") as handle:
		handle.write(response.read())

def generate_mp3(
	text: str,
	out_dir: Path,
	*,
	voice: str = "julie",
	eid: int | None = None,
	lid: int | None = None,
	vid: int | None = None,
	acc: int = 9066743,
	scene_id: int | None = None,
	ext: str = "mp3",
	fname: str = "",
	http_err: str = "",
	text_is_encoded: bool = False,
) -> Path:
	eid, lid, vid, scene_id = resolve_voice_params(
		voice=voice,
		eid=eid,
		lid=lid,
		vid=vid,
		scene_id=scene_id,
	)

	url = build_oddcast_url(
		text=text,
		eid=eid,
		lid=lid,
		vid=vid,
		acc=acc,
		scene_id=scene_id,
		ext=ext,
		fname=fname,
		http_err=http_err,
		text_is_encoded=text_is_encoded,
	)

	decoded_text = unquote(text) if text_is_encoded else text
	filename = f"{_sanitize_filename(decoded_text)}.{ext}"
	output_path = out_dir / filename
	download_mp3(url, output_path)
	return output_path


def generate_mp3_to_path(
	text: str,
	output_path: Path,
	*,
	voice: str = "julie",
	eid: int | None = None,
	lid: int | None = None,
	vid: int | None = None,
	acc: int = 9066743,
	scene_id: int | None = None,
	ext: str = "mp3",
	fname: str = "",
	http_err: str = "",
	text_is_encoded: bool = False,
) -> Path:
	eid, lid, vid, scene_id = resolve_voice_params(
		voice=voice,
		eid=eid,
		lid=lid,
		vid=vid,
		scene_id=scene_id,
	)
	url = build_oddcast_url(
		text=text,
		eid=eid,
		lid=lid,
		vid=vid,
		acc=acc,
		scene_id=scene_id,
		ext=ext,
		fname=fname,
		http_err=http_err,
		text_is_encoded=text_is_encoded,
	)
	download_mp3(url, output_path)
	return output_path

def _parse_args(argv: list[str]) -> argparse.Namespace:
	parser = argparse.ArgumentParser(description="Download Oddcast MP3 by TXT.")
	parser.add_argument("text", help="Text for the TXT parameter.")
	parser.add_argument(
		"--out-dir",
		default="output/raw_audio",
		help="Directory to write the MP3 file.",
	)
	parser.add_argument(
		"--voice",
		default="julie",
		choices=sorted(VOICE_PRESETS.keys()),
		help="Voice preset to use.",
	)
	parser.add_argument("--eid", type=int)
	parser.add_argument("--lid", type=int)
	parser.add_argument("--vid", type=int)
	parser.add_argument("--acc", type=int, default=9066743)
	parser.add_argument("--scene-id", type=int)
	parser.add_argument("--ext", default="mp3")
	parser.add_argument("--fname", default="")
	parser.add_argument("--http-err", default="")
	parser.add_argument(
		"--text-encoded",
		action="store_true",
		help="Indicates that TXT is already URL-encoded.",
	)
	return parser.parse_args(argv)

def main(argv: list[str]) -> int:
	args = _parse_args(argv)
	output_path = generate_mp3(
		args.text,
		Path(args.out_dir),
		voice=args.voice,
		eid=args.eid,
		lid=args.lid,
		vid=args.vid,
		acc=args.acc,
		scene_id=args.scene_id,
		ext=args.ext,
		fname=args.fname,
		http_err=args.http_err,
		text_is_encoded=args.text_encoded,
	)
	print(str(output_path))
	return 0

if __name__ == "__main__":
	raise SystemExit(main(sys.argv[1:]))