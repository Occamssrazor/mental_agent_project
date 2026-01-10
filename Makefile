POETRY=poetry

install:
	$(POETRY) install

start-all:
	docker-compose up -d --build

pull:
	docker exec ollama_server ollama pull qwen2.5:1.5b

logs:
	docker-compose logs -f

stop:
	docker-compose down

clean:
	docker-compose down -v

test-agent:
	$(POETRY) run python -c "from src.mental_agent import MentalAgent; print(MentalAgent().chat_text('Мне тревожно и нет сил', tg_chat_id=123))"
