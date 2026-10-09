# Conventions (Python)

- **Poetry for every Python command.** `poetry run python|pytest|ruff|black|mypy|alembic|uvicorn`. Never bare.
- Python ≥ 3.12. Pydantic v2. Async everywhere a driver is async.
- Formatting: Black; isort; line length is per repo (88 or 100) and never mixed.
  Lint: ruff (`E, W, F, I, B, C4, UP`) or pylint 10/10 with the project plugin.
  Types: mypy strict on `src`/package and tests; type hints on every signature.
- Naming: `snake_case` functions/variables/modules/schema files; `PascalCase`
  classes; `UPPER_SNAKE_CASE` constants. API paths `kebab-case`; bodies and
  query params `snake_case`.
- One use case / entity / port / plugin per file. Files named after the symbol.
- Domain identifiers (`UserId`, `CaseId`) and value objects over raw UUIDs and
  primitives; enums over strings.
- Exceptions: a base domain exception; `NotFoundException`,
  `BusinessRuleException`, `ValidationException` in the application layer;
  adapters translate to transport.
- Lazy imports only in the composition root or inside `can_process`, each with
  a comment naming the cycle or optional dependency.
- `_try_import`-style discovery swallows `ImportError`/`AttributeError` only.
- Docstrings explain **why** (the incident, the invariant, the cycle), not
  what the next line does. Dates and incident references are welcome.
- An override site carries a line-scoped disable and a reason stating why the
  framework cannot do this.
- Commit messages: name moved ratchet counts and why; name the golden chunks
  used to validate a prompt change; name the baseline regenerated.
- Pre-commit: ruff/black/isort/mypy (backend), eslint/prettier/tsc (frontend),
  secrets detection, large-file block, YAML/JSON validation, `codegen:check`.
- Environment: no hardcoded URLs or secrets; `settings` from env; CORS locked
  down outside dev.
- Document ownership: multi-agent repos keep a file-ownership matrix; an agent
  edits only files it owns and escalates for the rest.
