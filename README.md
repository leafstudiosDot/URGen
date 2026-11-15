# URGen

Generate a faceless portrait video from a text prompt.
Uses local Ollama (text), Oddcast (TTS), Whisper (subtitles), and ffmpeg (rendering).

## Prerequisites

- Python 3.10+ recommended
- ffmpeg installed and available on PATH
- Ollama running locally with a model like "mistral"

## Install

```bash
pip install -r requirements.txt
```

## Run the pipeline

```bash
python main.py "topic" --voice daniel --model gpt-oss:120b-cloud
```

## Outputs

- output/raw_audio: generated mp3 and script text
- output/raw_video: generated SRT subtitles
- output/final_shorts: final portrait mp4

## Backgrounds and music (randomized)

Place MP4 backgrounds in assets/backgrounds and MP3 music in assets/music.
For each run, the pipeline picks a random music track and loops random
backgrounds until the narration ends.

If you want to force a specific background instead of random selection:

```bash
python main.py "topic" --background assets/backgrounds/bg.mp4
```

## Oddcast TTS standalone

```bash
python tts/oddcast.py "Hello, Im Medico" --voice julie
```

## Auto upload (YouTube / TikTok)

Fill in `.env` (see `.env.example`) with your API credentials, then:

```bash
# Upload an already rendered video
python -m upload.run output/final_shorts/video.mp4 --title "My title" --platforms youtube,tiktok

# Or upload directly from the pipeline
python main.py "topic" --upload youtube,tiktok
```

YouTube uses a refresh token (YOUTUBE_CLIENT_ID/SECRET/REFRESH_TOKEN). TikTok uses TIKTOK_CLIENT/SECRET plus an access/refresh token.
