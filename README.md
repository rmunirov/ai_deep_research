# Deep Research Agent

AI-агент для многошагового исследования произвольных тем по текстовому запросу.
Построен на [Deep Agents SDK](https://docs.langchain.com/oss/python/deepagents/overview),
LangChain/LangGraph, FastAPI и Rich CLI.

## Архитектура

```
CLI (Typer + Rich)  →  FastAPI API  →  ResearchService
                                            │
                                    Orchestrator Agent
                                    (create_deep_agent)
                                            │
                          ┌─────────────────┼─────────────────┐
                      Planner          Searcher           NoteTaker
                      Analyst          Writer             Reviewer
                          │                │                  │
                     plan.md      Tavily/ArXiv/Wiki    notes/*.md
                                                       report.md
```

## Установка

```bash
# Клонировать и установить
git clone <repo-url>
cd deepResearchAgent
uv sync

# Настроить переменные окружения
cp .env.example .env
# Отредактировать .env: DR_TAVILY_API_KEY, DR_DATABASE_URL, и т.д.
```

## Требования

- Python >= 3.11
- PostgreSQL >= 15
- API-ключ Tavily (https://tavily.com)
- API-ключ LLM-провайдера (Anthropic / OpenAI / Google / ...)

## База данных

```bash
# Создать БД
createdb deep_research

# Применить миграции
alembic upgrade head
```

## Использование

### CLI

```bash
# Запустить исследование
research run "Сравнение подходов к RAG в 2026 году" --depth standard

# Быстрое исследование
research run "Что такое LangGraph?" --depth quick --no-interact

# Список исследований
research list
research list --status completed

# Статус конкретного исследования
research status <id>

# Возобновить прерванное
research resume <id>

# Экспорт отчёта
research export <id> --format html
research export <id> --format pdf

# Конфигурация
research config
research config set default_model "openai:gpt-5.2"

# Запуск API сервера
research serve
research serve --port 8080 --reload
```

### API

При запущенном сервере (`research serve`):

```bash
# Документация
open http://127.0.0.1:8000/docs

# Запустить исследование
curl -X POST http://127.0.0.1:8000/api/v1/research \
  -H "Content-Type: application/json" \
  -d '{"query": "Тема", "depth": "standard"}'

# Список
curl http://127.0.0.1:8000/api/v1/research

# SSE-стрим прогресса
curl http://127.0.0.1:8000/api/v1/research/{id}/events
```

## Конфигурация

Иерархия: defaults → `~/.config/deep-research/config.yaml` → `.env` → CLI flags.

| Переменная | Описание | По умолчанию |
|-----------|----------|--------------|
| `DR_DEFAULT_MODEL` | LLM-модель | `anthropic:claude-sonnet-4-6` |
| `DR_TAVILY_API_KEY` | API-ключ Tavily | — |
| `DR_DATABASE_URL` | URL PostgreSQL | `postgresql+asyncpg://...` |
| `DR_RESEARCHES_DIR` | Каталог артефактов | `./researches` |
| `DR_LANGUAGE` | Язык отчётов | `ru` |

## Структура артефактов

```
researches/{id}/
├── plan.md              # План исследования
├── notes/
│   ├── 001-topic.md     # Структурированные заметки (YAML + MD)
│   ├── 002-topic.md
│   └── ...
├── sources/
│   └── sources.json     # Индекс источников
├── report.md            # Итоговый отчёт
└── export/
    ├── report.html
    └── report.pdf
```

## Разработка

```bash
# Линтинг
uv run ruff check src/

# Проверка типов
uv run mypy src/

# Тесты
uv run pytest
```

## Лицензия

MIT
