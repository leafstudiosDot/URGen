import json
import re

from ollama import chat

def generate_script(topic: str, *, model: str = "mistral") -> str:
    print(f"[script] Generating script with model: {model}")
    prompt = f"""
    Write a spoken story for a 9:16 short (40 seconds to 5 minutes).
    Requirements:
    - no headings, no scene directions, no character labels
    - no narrator tags or script formatting
    - single block of text, as if one person is telling a story aloud
    - act like an influencer telling a story to their followers, with a hook, engaging storytelling, and an ending
    - in every paragraph, add a new line break after 2-3 sentences to create natural pauses for breath and emphasis
    - the story should be about the following topic, but feel free to take creative liberties with.
    - Never ask for like, share and follow or say anything about subscribing or following
    - skip saying anything about "Sure, I'll provide a story about {topic}" or similar, just start telling the story right away." just tell the story as if you are an influencer talking to your followers on a social media platform, with a hook, engaging storytelling, and an ending.
    Topic: {topic}
    """

    content_parts: list[str] = []
    print("[script] Streaming output:")
    for chunk in chat(model=model, messages=[
        {"role": "user", "content": prompt}
    ], stream=True):
        token = chunk.get("message", {}).get("content", "")
        if token:
            print(token, end="", flush=True)
            content_parts.append(token)

    content = "".join(content_parts)
    print("\n[script] Done. Length: {0} chars".format(len(content)))
    return content

def generate_metadata(topic: str, script_text: str, *, model: str = "mistral") -> dict:
    import json, re
    print(f"[metadata] Generating metadata with model: {model}")
    prompt = (
        "You are a social media manager. Given a short-form video topic and script, produce "
        "metadata for YouTube Shorts and TikTok. Return ONLY a valid JSON object with keys: "
        '{"title": "catchy title under 90 chars", "description": "2-4 sentence description for YouTube", '
        '"tags": ["tag1", "tag2"], "hashtags": ["#tag1", "#tag2"], '
        '"youtube_privacy": "public", "tiktok_privacy": "PUBLIC_TO_EVERYONE"}\n'
        f"Topic: {topic}\nScript: {script_text[:1500]}"
    )
    content = ""
    try:
        response = chat(model=model, messages=[{"role": "user", "content": prompt}], stream=False)
        if isinstance(response, dict):
            content = response.get("message", {}).get("content", "") or ""
        elif hasattr(response, "message"):
            content = getattr(response.message, "content", "") or ""
    except Exception as exc:
        print(f"[metadata] LLM call failed: {exc}")
        content = ""

    text = content.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        text = text[start : end + 1]
    try:
        data = json.loads(text)
    except Exception:
        data = {}

    title = str(data.get("title") or topic).strip()[:90]
    description = str(data.get("description") or topic).strip()
    tags = data.get("tags") or [topic]
    tags = [str(t).strip() for t in tags if str(t).strip()][:15]
    hashtags = data.get("hashtags") or []
    hashtags = [str(h).strip() for h in hashtags if str(h).strip()][:10]
    yt_privacy = data.get("youtube_privacy") or "public"
    tt_privacy = data.get("tiktok_privacy") or "PUBLIC_TO_EVERYONE"

    metadata = {
        "title": title,
        "description": description,
        "tags": tags,
        "hashtags": hashtags,
        "youtube_privacy": yt_privacy,
        "tiktok_privacy": tt_privacy,
    }
    print(f"[metadata] Title: {title}")
    return metadata
