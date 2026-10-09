# Enforcement

> Every architectural rule that had no executable check drifted. Every rule
> that had one held perfectly. (measured in one application, 2026-09-05: five stated
> rules with no check had 10, 12, 77, 203 and 17 violations; four rules with
> pre-commit + CI checks had zero.)

**A rule without a check is a suggestion.** Writing a rule down more
emphatically does not make it hold.

## 1. The ladder (strongest first)

| Rung | Mechanism | Example |
|---|---|---|
| 1. Impossible to express | type system / API surface | repository facade with no `.find()`; Go interfaces; generated endpoints that cannot skip ownership scoping |
| 2. Authoring-time lint | pylint/ESLint plugin, `golangci-lint` | project rules for raw reads, in-place mutation, adapter cross-imports; `errcheck`, `unused` |
| 3. Pre-commit | changed files only, before the commit exists | ruff/black/mypy/tsc/codegen:check |
| 4. CI ratchet | counts may fall, never rise | an architecture-drift script versus a committed baseline |

Prefer moving a rule **up** the ladder over restating it. Everything below
rung 1 compensates for an API that still permits the mistake.

## 2. The four layers of enforcement

1. **Make the compliant path the easiest path.** If adding an entity is "drop a
   JSON file" nobody hand-writes a controller that bypasses versioning. Low-code
   convergence is an enforcement strategy, not tidiness.
2. **Executable checks**: architecture ratchet, AST fitness tests, lint, types,
   API contract fuzzing, SAST, dependency audit.
3. **The ratchet** for debt too large to fix at once: each violation class is
   counted and compared against a committed baseline; any increase fails.
4. **Gates**: pre-commit (fast) and CI (blocking).

## 3. The ratchet

- Baseline file is committed (`architecture-baseline.json`, security
  baselines, schemathesis `check_baseline.json`).
- Counts may fall freely; any increase fails the build.
- Re-baseline **only** after a deliberate cleanup, in the same commit, with the
  reason in the commit message. Re-baselining to silence a new violation
  defeats the mechanism; if that becomes routine the ratchet is worthless.
- Track size metrics (controller LOC, page LOC, hand-written interfaces)
  **without gating** them: a check that fires on correct work trains people to
  ignore it. Gate only real violations.
- A baseline entry must be **narrower than the check** it mutes (match on a
  message substring, a glob, a named systemic defect). An entry that mutes more
  than the defect it names is a suppression wearing a ratchet's clothes.
- Systemic entries name the owning source location and why they are recorded
  rather than fixed.

## 4. Fitness tests

- Walk the **AST**, not grep. Grep misses `import x as y`, multi-name imports,
  and strings; AST sweeps found 13 of 13 pack-pickers where regex found 4.
- Core→adapter allowlist is **empty**. Adapter→adapter allowlist is explicit,
  one comment per entry naming file, module, and why.
- The test fails on a **stale** allowlist entry, so debt is visible and shrinks.
- A guard that has only ever been seen passing is not evidence. **Re-introduce
  the defect, watch it fail, revert.** Record that in the test docstring.
- Drift tests compare sibling implementations field by field (`ast.unparse`)
  and declare which differences are legitimate.

## 5. Override policy

### Class A — never override

| Rule | Why absolute |
|---|---|
| Never skip, xfail, or weaken a test | a skipped test looks like coverage and is not |
| Core must not import adapters | re-couples the domain to infrastructure; use a port |
| Never commit secrets | — |
| Identity is minted/compared/resolved by one function each | local normalisation silently forks identity |

If a Class A rule blocks you, the rule or the design is wrong. Raise it and
change it deliberately; do not disable it locally.

### Class B — overridable with justification

| Rule | Legitimate exception |
|---|---|
| No raw reads on versioned collections | a Tier 3 aggregation the helper cannot express, still filtering tombstones |
| No in-place mutations | an insert-only-by-nature collection |
| No adapter cross-imports | a time-boxed migration step naming the port that will replace it |
| Use a view spec, not a controller | the response shape cannot be reproduced and changing it breaks a contract |
| Case conversion in the mapping layer | a third-party payload the codegen does not own |

Not legitimate: "it was faster", "I don't know how the framework works", "the
check was annoying", "I'll clean it up later".

### Mechanics

1. Narrowest scope: line-level (`# pylint: disable-next=…`, `// nolint:…`,
   `# nosec B###`), never file- or project-level. No global skip lists in tool
   config.
2. The reason at the site says **why the framework cannot do this**, not what
   the line does.
3. If it moves a ratcheted count, the commit message says what was cleaned up
   or why the increase is justified.
4. Structural, permanent exemptions go in **one allowlist** with a comment per
   entry, not scattered comments.
5. Overrides are reviewed, not self-approved. A disable comment in a diff is a
   discussion prompt.

## 6. Adding a rule

1. Write the check first (ratchet `CHECKS` entry, lint checker, or fitness
   test).
2. Baseline existing violations rather than blocking all work on a cleanup.
3. State the rule in the rules file **and name the check**, so the reader gets
   a fast failing signal instead of prose.
4. Prefer the strongest practical rung.

## 7. Security scanning (same three-tier shape)

| Tier | Behaviour |
|---|---|
| Hard gate | a severity that is actionable **and green today**; cannot be baselined away |
| Ratchet | any new finding at any severity fails; today's findings are recorded and may only shrink |
| Report | `continue-on-error`; debt the gates deliberately do not block on stays visible |

Do not turn on a gate whose current failure set is unknown; triage first, then
promote in the same change that records the triage. Scope dependency gates to
the **production** tree; dev-toolchain CVEs are reported, not gated.

## 8. Agents

Every agent works under this policy. Two specifics:

- **Do not invent an exception silently.** A legitimate Tier 3 case is fine;
  say so in the report with the reason. The unreported bypass is the failure
  mode.
- **Do not touch a rule you do not own.** If a shared fixture, allowlist, or
  baseline must change to unblock you, escalate rather than editing it.
