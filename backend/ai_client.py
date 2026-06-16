import os
from openai import OpenAI

_client = None

def get_openai_client() -> OpenAI:
    """Lazily initialize and return a singleton OpenAI client."""
    global _client
    if _client is None:
        api_key = os.environ.get("OPENROUTER_API_KEY", "")
        _client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key
        )
    return _client

def generate_content(prompt: str) -> str:
    """Generate content from the AI model (openai/gpt-4o-mini) using OpenRouter."""
    try:
        client = get_openai_client()
        response = client.chat.completions.create(
            model="openai/gpt-4o-mini",
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=200,
            timeout=10.0
        )
        return response.choices[0].message.content
    except Exception as e:
        print("AI ERROR:", e)
        return "Sorry, something went wrong."
