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