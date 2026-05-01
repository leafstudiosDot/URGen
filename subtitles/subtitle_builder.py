from __future__ import annotations

from pathlib import Path

def format_subtitles(segments: list[dict]) -> list[dict]:
    subs = []

    for seg in segments:
        subs.append(
            {
                "start": float(seg["start"]),
                "end": float(seg["end"]),
                "text": str(seg["text"]).strip(),
                "words": seg.get("words"),
            }
        )

    return subs

def _chunk_words(text: str, max_words: int) -> list[str]:
    words = text.split()
    return [" ".join(words[i : i + max_words]) for i in range(0, len(words), max_words)]

def _format_timestamp(seconds: float) -> str:
    ms = int(round(seconds * 1000))
    hrs = ms // 3_600_000
    ms %= 3_600_000
    mins = ms // 60_000
    ms %= 60_000
    secs = ms // 1_000
    ms %= 1_000
    return f"{hrs:02}:{mins:02}:{secs:02},{ms:03}"

def write_srt(segments: list[dict], output_path: Path, *, max_words: int = 8) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    subtitle_index = 1
    for seg in format_subtitles(segments):
        words = seg.get("words") if isinstance(seg, dict) else None
        if words:
            for chunk in _chunk_words_with_timing(words, max_words):
                lines.append(str(subtitle_index))
                lines.append(
                    f"{_format_timestamp(chunk['start'])} --> {_format_timestamp(chunk['end'])}"
                )
                lines.append(chunk["text"])
                lines.append("")
                subtitle_index += 1
            continue

        chunks = _chunk_words(seg["text"], max_words)
        if not chunks:
            continue

        start_time = float(seg["start"])
        end_time = float(seg["end"])
        duration = max(end_time - start_time, 0.2)
        chunk_duration = duration / len(chunks)

        for chunk in chunks:
            chunk_end = start_time + chunk_duration
            lines.append(str(subtitle_index))
            lines.append(
                f"{_format_timestamp(start_time)} --> {_format_timestamp(chunk_end)}"
            )
            lines.append(chunk)
            lines.append("")
            subtitle_index += 1
            start_time = chunk_end

    output_path.write_text("\n".join(lines), encoding="utf-8")
    return output_path

def _chunk_words_with_timing(words: list[dict], max_words: int) -> list[dict]:
    chunks: list[dict] = []
    buffer: list[dict] = []
    for word in words:
        if not word.get("word"):
            continue
        buffer.append(word)
        if len(buffer) >= max_words:
            chunks.append(_build_chunk_from_words(buffer))
            buffer = []
    if buffer:
        chunks.append(_build_chunk_from_words(buffer))
    return chunks

def _build_chunk_from_words(words: list[dict]) -> dict:
    start = float(words[0].get("start", 0.0))
    end = float(words[-1].get("end", start))
    text = " ".join(str(item.get("word", "")).strip() for item in words).strip()
    return {
        "start": start,
        "end": max(end, start + 0.05),
        "text": text,
    }