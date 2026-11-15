# Agent Guide for URGen Project

## Quick Start Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run the pipeline (single use)
python main.py "topic" --voice julie

# Generate specific background
python main.py "topic" --background assets/backgrounds/bg.mp4

# Run TTS standalone
python tts/oddcast.py "Hello, Im Medico" --voice julie
```

## Architecture Overview

- **Entry Point**: `main.py` → `urgen.orchestrator. Orchestrator.run()`
- **Core Module**: `core/` - Pipeline orchestrator, config management
- **Package Boundaries (Monorepo)**:
  - `core/`: Main orchestration (config, orchestrator)
  - `scripts/`: Script generator utility
  - `tts/`: Oddcast audio generation
  - `subtitles/`: Whisper subtitle builder
  - `video/`: FFmpeg video builder

## Development Workflow

### Standard Pipeline Run
```bash
python main.py topic_name --voice julie
```

### Key Commands to Inspect:
- `core/` modules for configuration and orchestration logic
- `scripts/script_generator.py` for script generation commands
- `video/ffmpeg_builder.py` for video rendering commands
- `upload/tiktok/__init__.py` for TikTok upload workflow
- `upload/youtube/__init__.py` for YouTube pipeline

## Important Workflow Rules

1. **Git is READ-only only in your local checkout** - Do not attempt to modify git history or commit new files

## Output Structure

output/
├── raw_audio/          # Generated audio + text
│   └── <filename>.mp3
├── raw_video/          # Raw video for processing (processed .srt)
│   └── <file_suffixes>.srt
└── final_shorts/       # Final rendered output (uploaded mp4)
    ├── <filenames>.mp4  (YouTube/TikTok uploads, with title)

## Configuration File Paths
- Pipeline config: `core/config.py`
- Scene orchestration: `core/orchestrator.py`
- Video processing: `video/video_editor.py`, `video/ffmpeg_builder.py`

## Prerequisites Summary

| Component | Requirement | Notes |
|-----------|-------------|-------|
| Python | 3.10+ | Required |
| Ollama | "mistral" or similar | For text LLM |
| FFmpeg | Available in PATH | Video rendering |
| ffmpeg-python | Installed | Pipeline integration |

## Package Ownership (Monorepo Structure)

- **Core**: `core/` - orchestrator, config, pipeline orchestration
- **TTS**: `tts/` - Oddcast TTS API client and generation
- **Subtitles**: `subtitles/` - Whisper subtitle builder engine  
- **Video**: `video/` - FFmpeg video builder and editor
