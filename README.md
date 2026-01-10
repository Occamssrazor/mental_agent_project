# 🧠 Mental Health Agent  
**LangGraph + RAG + Dual LLM + Telegram**

Telegram-бот-агент для поддержки психического здоровья с агентной логикой, ветвлениями, ежедневными чек-инами и недельными обзорами.

👉 Бот в Telegram: **https://t.me/mentalhealthchat_bot**

---

## 📌 Возможности

- 🤖 **Агент на LangGraph** с явными состояниями и маршрутами
- 🧠 **Dual-LLM архитектура**
  - **Light LLM (Ollama)** — обычные диалоги, вопросы, поддержка
  - **Mental LLM (Qwen2.5-7B + LoRA, Unsloth)** — чек-ины, рекомендации, weekly review
- 📊 **Ежедневные чек-ины**: настроение / стресс / энергия (1–10)
- 🧭 **Агентность через ветвления**
  - высокий стресс → успокоение
  - низкая энергия → микро-шаги
  - низкое настроение → поддержка
- 📚 **RAG** (30+ карточек: CBT / ACT / DBT / дыхание / сон / прокрастинация)
- ⏰ **SLA-напоминания**: 24h / 48h / 72h
- 🗓 **Недельный обзор** с корректировкой плана
- 💾 **Postgres** (чек-ины, планы)
- 🔁 **Celery + Redis** (расписания)
- 🐳 **Полностью в Docker**
- 🔐 **Telegram webhook** с secret token

---

## 🏗 Архитектура (кратко)

```markdown


Telegram
↓
FastAPI (webhook)
↓
LangGraph (agent graph)
├─ intent: chat → Ollama (light LLM)
└─ intent: check-in → Qwen2.5-7B + LoRA (mental LLM)
↓
RAG (TF-IDF)
↓
рекомендации + plan_delta

```

---

## 📁 Структура проекта

```

mental_agent_project/
├── src/
│   ├── graph/              # LangGraph (state, nodes, prompts)
│   ├── llm_clients/        # Ollama + Unsloth LoRA
│   ├── rag/                # mental_database.json + retriever
│   ├── tools/              # LangChain tools (DB, Telegram)
│   ├── scheduler.py        # Celery: reminders, nudges, weekly
│   ├── telegram_api.py     # FastAPI webhook
│   └── mental_agent.py     # агент-обёртка
├── lora/
│   └── grpo_lora/          # adapter_config.json + adapter_model.safetensors
├── docker-compose.yml
├── Dockerfile.api
├── Dockerfile.worker       # GPU worker
├── pyproject.toml
├── Makefile
├── .env                    # СЕКРЕТЫ (не коммитить!)
└── README.md

```
---


## 🔐 Переменные окружения (`.env`)

Создай файл `.env` в корне проекта:

```env
# Telegram
TG_BOT_TOKEN=1234567890:AAxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TG_WEBHOOK_SECRET=long_random_secret_string

# Light LLM (Ollama)
LIGHT_PROVIDER=ollama
LIGHT_MODEL=qwen2.5:1.5b
OLLAMA_BASE_URL=http://ollama:11434/v1

# Mental LLM (LoRA)
MENTAL_BASE_MODEL=unsloth/Qwen2.5-7B-Instruct
MENTAL_LORA_PATH=/app/lora/grpo_lora

# Infrastructure
DATABASE_URL=postgresql+psycopg://app:app@db:5432/mental_agent
REDIS_URL=redis://redis:6379/0
```
⚠️ Добавь в .gitignore:

```
.env
lora/
```

### Рекомендуемый способ сохранения

```python
model.save_pretrained("grpo_lora", safe_serialization=True)
tokenizer.save_pretrained("grpo_lora")
````

В папке `grpo_lora/` **обязательно** должны появиться файлы:

* `adapter_config.json`
* `adapter_model.safetensors`

> ⚠️ Если сохранить только через `model.save_lora(...)`,
> `adapter_config.json` может **не создаться** — тогда worker не сможет загрузить LoRA.

В `docker-compose.yml` эта папка монтируется так:

```yaml
volumes:
  - ./lora:/app/lora:ro
```

Внутри контейнера worker путь будет:

```
/app/lora/grpo_lora
```

Именно его нужно указывать в `.env`:

```env
MENTAL_LORA_PATH=/app/lora/grpo_lora
```

---

## 🚀 Запуск проекта

### 1️⃣ Требования

* Docker
* Docker Compose
* GPU с установленным **NVIDIA Container Toolkit** (для mental LLM)

Проверка GPU:

```bash
docker run --gpus all nvidia/cuda:12.1.0-base nvidia-smi
```

---

### 2️⃣ Запуск всех сервисов

```bash
make start-all
```

Будут запущены:

* **Ollama** — light LLM (`http://localhost:11434`)
* **Postgres** — база данных
* **Redis** — брокер Celery
* **FastAPI** — Telegram webhook
* **Celery worker** — LangGraph + LoRA (GPU)

---

### 3️⃣ Загрузка light-модели (один раз)

```bash
make pull
```

По умолчанию загружается:

```
qwen2.5:1.5b
```

Можно заменить на любую другую модель Ollama.

---

## 🌐 Telegram Webhook

Для работы webhook нужен **публичный HTTPS URL**
(например: ngrok, cloudflare tunnel, VPS).

### Пример с ngrok

```bash
ngrok http 8000
```

Ты получишь URL вида:

```
https://abcd-1234.ngrok-free.app
```

---

### Установка webhook

```bash
curl -X POST "https://api.telegram.org/bot$TG_BOT_TOKEN/setWebhook" \
  -d "url=https://YOUR_DOMAIN/tg/webhook" \
  -d "secret_token=$TG_WEBHOOK_SECRET"
```

FastAPI проверяет заголовок:

```
X-Telegram-Bot-Api-Secret-Token
```

---

## 💬 Как пользоваться ботом

### 🟢 Обычный чат (light LLM — Ollama)

Примеры сообщений:

```
Мне тревожно
Что делать, если нет сил?
Почему я прокрастинирую?
```

→ Ответ формируется **через Ollama**, без тяжёлой модели.

---

### 🟣 Чек-ин (mental LLM + RAG)

Поддерживаются разные форматы:

```
7 8 3
```

или:

```
Настроение 4, стресс 7, энергия 3. Сегодня весь день тревожно.
```

Бот:

1. Распознаёт чек-ин
2. Парсит числа через LoRA
3. Выбирает ветку:

   * высокий стресс → успокоение
   * низкая энергия → микро-шаг
   * низкое настроение → поддержка
4. Подбирает упражнения через RAG
5. Может скорректировать план дня

---

## ⏰ Напоминания и SLA

* 🕐 Ежедневный чек-ин — **13:00 по МСК**
* Если пользователь не отвечает:

  * **24 часа** — мягкий пинг
  * **48 часов** — выбор без дневника
  * **72 часа** — предложение паузы

---

## 📅 Weekly review

Раз в неделю агент:

* анализирует чек-ины за 7 дней
* пишет обзор состояния
* обновляет план пользователя

---

## ⚙️ Команды Telegram

| Команда   | Описание                |
| --------- | ----------------------- |
| `/pause`  | Поставить бота на паузу |
| `/resume` | Возобновить             |
| `/plan`   | Показать текущий план   |

---

## 🐛 Отладка и частые проблемы

### ❌ Бот не отвечает

Проверь логи API:

```bash
docker-compose logs api
```

Проверь:

* webhook установлен
* HTTPS URL
* `TG_BOT_TOKEN` корректный

---

### ❌ Ошибка загрузки LoRA

Проверь:

```bash
ls lora/grpo_lora
```

Должны быть:

* `adapter_config.json`
* `adapter_model.safetensors`

---

### ❌ CUDA / GPU не виден

```bash
docker-compose logs worker
```

И проверь GPU:

```bash
docker run --gpus all nvidia/cuda:12.1.0-base nvidia-smi
```

---

### ❌ Postgres / Redis

Их **не нужно устанавливать локально**.
Они запускаются внутри Docker.

Проверь:

```bash
docker ps
```

---

## ⚠️ Этика и ограничения

Бот **не является медицинским специалистом**:

* не ставит диагнозы
* не заменяет терапию
* предлагает только мягкие и безопасные шаги

---