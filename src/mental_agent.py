from src.config import OLLAMA_BASE_URL, LIGHT_MODEL, MENTAL_BASE_MODEL, MENTAL_LORA_PATH
from src.llm_clients.ollama_client import OllamaClient
from src.llm_clients.local_unsloth_lora import LocalUnslothLoRA
from src.llm_clients.router import LLMRouter
from src.rag.retriever_tfidf import MentalRetriever
from src.graph.build_graph import build_graph

class MentalAgent:
    def __init__(self):
        self.retriever = MentalRetriever("src/rag/mental_database.json")

        light = OllamaClient(base_url=OLLAMA_BASE_URL)
        mental = LocalUnslothLoRA(base_model=MENTAL_BASE_MODEL, lora_path=MENTAL_LORA_PATH)

        self.router = LLMRouter(light_client=light, mental_client=mental, light_model=LIGHT_MODEL)
        self.graph = build_graph(self.router, self.retriever)

    def invoke(self, state: dict):
        return self.graph.invoke(state)

    def chat_text(self, text: str, tg_chat_id: int, user_id: int = 1):
        state = {
            "user_id": user_id,
            "tg_chat_id": tg_chat_id,
            "timezone": "Europe/Moscow",
            "event": "user_message",
            "text": text,
            "rag_top_k": 5,
        }
        return self.graph.invoke(state)
