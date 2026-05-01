from ollama import chat

def generate_script(topic: str, *, model: str = "mistral") -> str:
    prompt = f"""
    Write a spoken story for a 9:16 short (40 seconds to 5 minutes).
    Requirements:
    - strong hook in first sentence
    - emotional tension
    - fast pacing
    - cliffhanger ending
    - no headings, no scene directions, no character labels
    - no narrator tags or script formatting
    - single block of text, as if one person is telling a story aloud
    Topic: {topic}
    """

    response = chat(model=model, messages=[
        {"role": "user", "content": prompt}
    ])

    return response["message"]["content"]