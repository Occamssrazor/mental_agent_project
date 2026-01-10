import json, re
from typing import Any, Dict
from vllm import SamplingParams

SOLUTION_RE = re.compile(r"<SOLUTION>\s*(.*?)\s*</SOLUTION>", re.DOTALL)

def extract_solution_json(text: str) -> Dict[str, Any]:
    m = SOLUTION_RE.search(text or "")
    if not m:
        raise ValueError("No <SOLUTION> found")
    payload = m.group(1).strip().strip("`")
    if payload.lower().startswith("json"):
        payload = payload[4:].strip()
    return json.loads(payload)

class LocalUnslothLoRA:
    def __init__(self, base_model: str, lora_path: str, max_seq_length: int = 8192):
        from unsloth import FastLanguageModel
        from peft import PeftModel

        model, tokenizer = FastLanguageModel.from_pretrained(
            model_name=base_model,
            max_seq_length=max_seq_length,
            load_in_4bit=False,
            fast_inference=True,
            gpu_memory_utilization=0.6,
        )

        model = PeftModel.from_pretrained(model, lora_path, is_trainable=False)
        model.eval()
        try:
            model = FastLanguageModel.for_inference(model)
        except Exception:
            pass

        self.model = model
        self.tokenizer = tokenizer
        self.sampling = SamplingParams(temperature=0.3, top_k=50, max_tokens=512)

    def generate(self, user_text: str) -> str:
        prompt = self.tokenizer.apply_chat_template(
            [{"role": "user", "content": user_text}],
            tokenize=False,
            add_generation_prompt=True,
        )
        out = self.model.fast_generate({"prompt": prompt}, self.sampling)
        return out[0].outputs[0].text

    def generate_json(self, user_text: str, repair_attempts: int = 1) -> Dict[str, Any]:
        raw = self.generate(user_text)
        try:
            return extract_solution_json(raw)
        except Exception:
            if repair_attempts <= 0:
                raise
        repair_prompt = (
            "Fix the JSON inside <SOLUTION>...</SOLUTION>. Return ONLY <SOLUTION>fixed_json</SOLUTION>.\n\n"
            f"Broken output:\n{raw}"
        )
        raw2 = self.generate(repair_prompt)
        return extract_solution_json(raw2)

