# Python rules

Read `shared/` first. These files add the Python idiom for each rung of the
ladder.

| File | Rung | Source |
|---|---|---|
| `01-ddd-ports-adapters.md` | Level 0: classical DDD + Ports & Adapters | a hand-written application |
| `02-schema-driven-framework.md` | Levels 2–3: schema-driven app and library | [slip-stream](https://github.com/digitally-rendered/slip-stream) and an application built on it |
| `03-plugin-pipeline.md` | Level 1: plugin ensemble, pipeline, LLM adapters | a pipeline application |
| `04-testing.md` | all | all sources |
| `05-conventions.md` | all | all sources |

Stack assumed: Python ≥ 3.12, Poetry, FastAPI, Pydantic v2, Motor or
SQLAlchemy 2 (async), pytest + pytest-asyncio.
