"""Auto-upload helpers for YouTube and TikTok."""

from __future__ import annotations

from upload.youtube import upload_video as upload_youtube
from upload.tiktok import upload_video as upload_tiktok

__all__ = ["upload_youtube", "upload_tiktok"]
