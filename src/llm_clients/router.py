from typing import Dict

class LLMRouter:
    def __init__(self, light_client, mental_client, light_model: str):
        self.light = light_client
        self.mental = mental_client
        self.light_model = light_model

    def light_chat(self, system: str, user: str) -> str:
        msgs = [{"role": "system", "content": system}, {"role": "user", "content": user}]
        return self.light.chat_completion(msgs, model=self.light_model, temperature=0.7, max_tokens=512)

    def mental_json(self, prompt: str) -> Dict:
        return self.mental.generate_json(prompt, repair_attempts=1)

