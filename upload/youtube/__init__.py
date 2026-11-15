"""YouTube Data API v3 auto-upload helper.

Supports unattended uploads using a refresh token (recommended) or an
interactive OAuth flow backed by a client secrets file.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

from upload.common import env, require_env

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"


def _client_config_from_env() -> dict[str, Any] | None:
    client_id = env("YOUTUBE_CLIENT_ID")
    client_secret = env("YOUTUBE_CLIENT_SECRET")
    if client_id and client_secret:
        return {
            "installed": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": ["http://localhost"],
            }
        }
    return None


def get_credentials(
    *,
    client_secrets_file: str | None = None,
    token_file: str | None = None,
):
    """Return google.oauth2.credentials.Credentials for YouTube upload."""
    try:
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(
            "google-auth is required. Install: pip install google-auth google-auth-oauthlib google-api-python-client"
        ) from exc

    # 1) Unattended: refresh token from env.
    refresh_token = env("YOUTUBE_REFRESH_TOKEN")
    client_id = env("YOUTUBE_CLIENT_ID")
    client_secret = env("YOUTUBE_CLIENT_SECRET")
    if refresh_token and client_id and client_secret:
        creds = Credentials(
            token=None,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=client_id,
            client_secret=client_secret,
            scopes=SCOPES,
        )
        if not creds.valid:
            creds.refresh(Request())
        return creds

    # 2) Token file (saved from a previous interactive flow).
    token_path = Path(token_file or env("YOUTUBE_TOKEN_FILE", "youtube_token.json"))
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            token_path.write_text(creds.to_json(), encoding="utf-8")
        if creds and creds.valid:
            return creds

    # 3) Interactive flow using client secrets.
    secrets_path = Path(
        client_secrets_file
        or env("YOUTUBE_CLIENT_SECRETS_FILE", "client_secrets.json")
    )
    if not secrets_path.exists():
        cfg = _client_config_from_env()
        if cfg is None:
            raise RuntimeError(
                "YouTube credentials missing. Set YOUTUBE_REFRESH_TOKEN + "
                "YOUTUBE_CLIENT_ID + YOUTUBE_CLIENT_SECRET in .env, or provide "
                "client_secrets.json / YOUTUBE_CLIENT_SECRETS_FILE."
            )
        # Write a temporary secrets file for the flow.
        secrets_path = Path("client_secrets.json")
        secrets_path.write_text(json.dumps(cfg), encoding="utf-8")

    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
    except Exception as exc:  # pragma: no cover
        raise RuntimeError("google-auth-oauthlib is required.") from exc

    flow = InstalledAppFlow.from_client_secrets_file(str(secrets_path), SCOPES)
    creds = flow.run_local_server(port=0)
    out_path = Path(token_file or env("YOUTUBE_TOKEN_FILE", "youtube_token.json"))
    out_path.write_text(creds.to_json(), encoding="utf-8")
    print(f"[youtube] Saved credentials to {out_path}")
    return creds


def get_service(credentials=None):
    try:
        from googleapiclient.discovery import build
    except Exception as exc:  # pragma: no cover
        raise RuntimeError("google-api-python-client is required.") from exc
    if credentials is None:
        credentials = get_credentials()
    return build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, credentials=credentials)


def upload_video(
    video_path: str | Path,
    *,
    title: str,
    description: str = "",
    tags: list[str] | None = None,
    category_id: str = "22",
    privacy_status: str = "public",
    chunk_size: int = 1024 * 1024 * 5,
) -> dict[str, Any]:
    """Upload a video to YouTube and return the API response."""
    video_path = Path(video_path)
    if not video_path.exists():
        raise FileNotFoundError(f"Video not found: {video_path}")

    try:
        from googleapiclient.http import MediaFileUpload
    except Exception as exc:  # pragma: no cover
        raise RuntimeError("google-api-python-client is required.") from exc

    youtube = get_service()
    body = {
        "snippet": {
            "title": title[:100],
            "description": description,
            "tags": tags or [],
            "categoryId": category_id,
        },
        "status": {
            "privacyStatus": privacy_status,
            "selfDeclaredMadeForKids": False,
        },
    }

    media = MediaFileUpload(
        str(video_path),
        mimetype="video/mp4",
        resumable=True,
        chunksize=chunk_size,
    )
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"[youtube] Upload progress: {int(status.progress() * 100)}%")
    video_id = response.get("id")
    print(f"[youtube] Upload complete: https://youtu.be/{video_id}")
    return response


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Upload a video to YouTube.")
    parser.add_argument("video", help="Path to the video file.")
    parser.add_argument("--title", required=True, help="Video title.")
    parser.add_argument("--description", default="", help="Video description.")
    parser.add_argument("--tags", default="", help="Comma-separated tags.")
    parser.add_argument("--category-id", default="22", help="YouTube category id.")
    parser.add_argument(
        "--privacy",
        default="public",
        choices=["public", "unlisted", "private"],
        help="Privacy status.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv if argv is not None else sys.argv[1:])
    tags = [t.strip() for t in args.tags.split(",") if t.strip()]
    response = upload_video(
        args.video,
        title=args.title,
        description=args.description,
        tags=tags,
        category_id=args.category_id,
        privacy_status=args.privacy,
    )
    print(json.dumps(response, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
