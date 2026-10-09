# hexagonal-rules — agent guidance

This repository holds consolidated architecture rules. It contains no
application code.

## Sources

The rules were distilled from the public frameworks
[slip-stream](https://github.com/digitally-rendered/slip-stream), [stellar-drive](https://github.com/digitally-rendered/stellar-drive) and
[Syntact](https://github.com/digitally-rendered/Syntact) (TypeScript, in flight) and from several private
applications and a private knowledge workspace. **Only the three public
frameworks may be named in these files.** Private sources are described by
role (a classical DDD application, a schema-driven application, a
plugin-pipeline application, a personal knowledge workspace), never by
name, path, product, or person. Never copy private facts, personal data, or
domain content into this repository.

## Editing rules

- A rule states what and why, then names the check that enforces it. A rule
  with no enforceable check is written as SHOULD, not MUST, until a check exists.
- Do not restate a source's stage lists, commands, or counts; link to the
  concept and keep the rule durable. Counts and dates in these files are
  evidence of why a rule exists, not live state.
- When sources disagree, the more abstract rung of the ladder wins for
  framework concerns and the classical DDD rung wins for domain-modelling
  concerns. Record the disagreement in `shared/05-abstraction-ladder.md`.
- Keep examples minimal and domain-neutral.
- Per-language folders own language idioms. `shared/` owns anything that must be
  true in every language. If a rule appears in two language folders verbatim,
  move it to `shared/` and reference it.

## Structure

See `README.md` for the layout and the rule-strength vocabulary.
