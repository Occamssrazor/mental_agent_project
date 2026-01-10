from typing import Dict, List
from openai import OpenAI

class OllamaClient:
    def __init__(self, base_url: str):
        self.client = OpenAI(base_url=base_url, api_key="ollama")

    def chat_completion(self, messages: List[Dict[str, str]], model: str, temperature: float = 0.7, max_tokens: int = 512) -> str:
        resp = self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return resp.choices[0].message.content or ""
