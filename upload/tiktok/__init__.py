"""TikTok Content Posting API auto-upload helper.

Uses the direct-post flow (FILE_UPLOAD) with chunked upload. Requires a
valid access token with the `video.publish` / `video.upload` scopes.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

import requests

from upload.common import env, require_env

TIKTOK_API_BASE = "https://open.tiktokapis.com"
TOKEN_URL = f"{TIKTOK_API_BASE}/v2/oauth/token/"
INIT_URL = f"{TIKTOK_API_BASE}/v2/post/publish/video/init/"
STATUS_URL = f"{TIKTOK_API_BASE}/v2/post/publish/status/fetch/"

PRIVACY_LEVELS = [
    "PUBLIC_TO_EVERYONE",
    "MUTUAL_FOLLOW_FRIENDS",
    "FOLLOWER_OF_CREATOR",
    "SELF_ONLY",
]


def _client_key() -> str:
    return require_env("TIKTOK_CLIENT")


def _client_secret() -> str:
    return require_env("TIKTOK_SECRET")


def refresh_access_token(refresh_token: str | None = None) -> dict[str, Any]:
    """Refresh a TikTok access token. Returns the token response dict."""
    rt = refresh_token or env("TIKTOK_REFRESH_TOKEN")
    if not rt:
        raise RuntimeError("TIKTOK_REFRESH_TOKEN is required to refresh.")
    data = {
        "client_key": _client_key(),
        "client_secret": _client_secret(),
        "grant_type": "refresh_token",
        "refresh_token": rt,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    resp = requests.post(TOKEN_URL, data=data, headers=headers, timeout=60)
    resp.raise_for_status()
    payload = resp.json()
    if "access_token" in payload:
        os.environ["TIKTOK_ACCESS_TOKEN"] = payload["access_token"]
        if "refresh_token" in payload:
            os.environ["TIKTOK_REFRESH_TOKEN"] = payload["refresh_token"]
    return payload


def get_access_token() -> str:
    token = env("TIKTOK_ACCESS_TOKEN")
    if token:
        return token
    # Try refreshing.
    payload = refresh_access_token()
    token = payload.get("access_token")
    if not token:
        raise RuntimeError(f"Failed to obtain TikTok access token: {payload}")
    return token


def _init_upload(
    *,
    access_token: str,
    video_size: int,
    chunk_size: int,
    total_chunks: int,
    title: str,
    privacy_level: str,
    disable_duet: bool = False,
    disable_comment: bool = False,
    disable_stitch: bool = False,
) -> dict[str, Any]:
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json; charset=UTF-8",
    }
    body = {
        "post_info": {
            "title": title[:150],
            "privacy_level": privacy_level,
            "disable_duet": disable_duet,
            "disable_comment": disable_comment,
            "disable_stitch": disable_stitch,
        },
        "source_info": {
            "source": "FILE_UPLOAD",
            "video_size": video_size,
            "chunk_size": chunk_size,
            "total_chunk_count": total_chunks,
        },
    }
    resp = requests.post(INIT_URL, headers=headers, json=body, timeout=60)
    resp.raise_for_status()
    payload = resp.json()
    if payload.get("error", {}).get("code") not in (None, "ok", "success"):
        raise RuntimeError(f"TikTok init failed: {payload}")
    return payload


def _upload_chunks(upload_url: str, video_path: Path, chunk_size: int) -> None:
    size = video_path.stat().st_size
    total_chunks = (size + chunk_size - 1) // chunk_size
    with open(video_path, "rb") as f:
        for i in range(total_chunks):
            start = i * chunk_size
            end = min(start + chunk_size, size) - 1
            chunk = f.read(chunk_size)
            headers = {
                "Content-Type": "video/mp4",
                "Content-Range": f"bytes {start}-{end}/{size}",
                "Content-Length": str(len(chunk)),
            }
            resp = requests.put(upload_url, headers=headers, data=chunk, timeout=300)
            if resp.status_code not in (200, 201, 206):
                raise RuntimeError(
                    f"TikTok chunk upload failed ({resp.status_code}): {resp.text}"
                )
            print(f"[tiktok] Uploaded chunk {i + 1}/{total_chunks}")


def _fetch_status(access_token: str, publish_id: str, *, timeout: int = 300) -> dict[str, Any]:
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json; charset=UTF-8",
    }
    deadline = time.time() + timeout
    while time.time() < deadline:
        resp = requests.post(
            STATUS_URL,
            headers=headers,
            json={"publish_id": publish_id},
            timeout=60,
        )
        resp.raise_for_status()
        payload = resp.json()
        data = payload.get("data", {})
        status = data.get("status")
        print(f"[tiktok] Status: {status}")
        if status in ("PUBLISH_COMPLETE", "FAILED", "SPAM_RISK_TOO_MANY_POSTS"):
            return payload
        time.sleep(5)
    raise TimeoutError("Timed out waiting for TikTok publish status.")


def upload_video(
    video_path: str | Path,
    *,
    title: str,
    privacy_level: str = "PUBLIC_TO_EVERYONE",
    disable_duet: bool = False,
    disable_comment: bool = False,
    disable_stitch: bool = False,
    chunk_size: int = 10 * 1024 * 1024,
) -> dict[str, Any]:
    """Upload a video to TikTok via direct post. Returns status payload."""
    video_path = Path(video_path)
    if not video_path.exists():
        raise FileNotFoundError(f"Video not found: {video_path}")
    if privacy_level not in PRIVACY_LEVELS:
        raise ValueError(f"privacy_level must be one of {PRIVACY_LEVELS}")

    access_token = get_access_token()
    size = video_path.stat().st_size
    total_chunks = max(1, (size + chunk_size - 1) // chunk_size)
    # Ensure chunk_size not larger than file for single-chunk uploads.
    if total_chunks == 1:
        chunk_size = size

    init_payload = _init_upload(
        access_token=access_token,
        video_size=size,
        chunk_size=chunk_size,
        total_chunks=total_chunks,
        title=title,
        privacy_level=privacy_level,
        disable_duet=disable_duet,
        disable_comment=disable_comment,
        disable_stitch=disable_stitch,
    )
    data = init_payload.get("data", {})
    publish_id = data.get("publish_id")
    upload_url = data.get("upload_url")
    if not publish_id or not upload_url:
        raise RuntimeError(f"TikTok init response missing fields: {init_payload}")

    print(f"[tiktok] Publish id: {publish_id}")
    _upload_chunks(upload_url, video_path, chunk_size)
    status_payload = _fetch_status(access_token, publish_id)
    print(f"[tiktok] Done: {status_payload}")
    return status_payload


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Upload a video to TikTok.")
    parser.add_argument("video", help="Path to the video file.")
    parser.add_argument("--title", required=True, help="Post title/caption.")
    parser.add_argument(
        "--privacy",
        default="PUBLIC_TO_EVERYONE",
        choices=PRIVACY_LEVELS,
        help="Privacy level.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv if argv is not None else sys.argv[1:])
    response = upload_video(
        args.video,
        title=args.title,
        privacy_level=args.privacy,
    )
    print(json.dumps(response, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
