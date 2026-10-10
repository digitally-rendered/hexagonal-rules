# `requirements.md` schema

## 1. Structure

```markdown
# Requirements Document                      ← exact title
**Feature:** <Feature Name>                  ← beneath the title
> ⚠️ Remediation pending (<date>) — …       ← banner only while a tracker item is open
> **Amendment (<date>):** …                  ← when another spec or decision changed this one

## Introduction
<what, for whom, why now; the invariant the subsystem exists to satisfy;
 evidence quality note when research-based; scope and out-of-scope>

## Glossary
- **Term_Name**: definition (Underscore_Case for domain terms used in criteria)

## Constraints              ← optional; non-negotiables that gate implementation
## Non-Goals                ← optional; what this spec deliberately does not do
## Dependency on Adjacent Specs   ← optional; what it consumes/feeds, by spec name and phase

## Requirements
### Requirement N: <Title>
**User Story:** As a <role>, I want <capability>, so that <outcome>.
**Schema:** `schemas/<entity>.json` (new | changed: <fields>) | `views/<view>.json` | operation `<schema>_<op>` | none: <reason>
#### Acceptance Criteria
1. WHEN <trigger> THEN THE system SHALL <response>
2. IF <condition> THEN THE system SHALL <response>
3. WHILE <state> THE system SHALL <response>
4. WHERE <feature is enabled> THE system SHALL <response>
5. THE <Component> SHALL <always-true property>
5a. <sub-criterion added by amendment keeps the parent number>
```

Older specs used `standards.md` (technical, security, performance, quality,
documentation standards). New specs put those in `design.md`; a README
records which convention a spec follows.

Large specs may split requirements by concern (`persona-requirements.md`,
`regulatory-requirements.md`, `technical-requirements.md`) with
prefixed ids (`P1`, `L1`, `T1`); `requirements.md` remains the index.

## 2. EARS grammar (Easy Approach to Requirements Syntax)

| Pattern | Form | Use |
|---|---|---|
| Ubiquitous | `THE <system/component> SHALL …` | always true; invariants, data shapes, retention floors |
| Event-driven | `WHEN <event> THEN THE system SHALL …` | the dominant form; a trigger and a required response |
| Unwanted behaviour | `IF <undesired condition> THEN THE system SHALL …` | errors, denials, failures |
| State-driven | `WHILE <state> THE system SHALL …` | behaviour during a mode |
| Optional feature | `WHERE <feature> THE system SHALL …` | configurable behaviour |
| Complex | `WHEN … IF … THEN THE system SHALL …` | compose sparingly |

- One criterion, one testable obligation. `SHALL` is the only modal;
  `SHALL NOT` for prohibitions. No "should", "may", "typically" inside a
  criterion.
- Name the actor and the component (`THE Authorization_Service SHALL …`), not
  "it".
- State the observable outcome, including status codes, field names, limits,
  time bounds, and exact user-facing wording where the wording is the
  requirement (disclaimers, labels).
- Negative and failure paths are criteria too: what is refused, what is
  logged, what does not happen.
- Security and privacy criteria say what **never** happens (`SHALL NOT
  contain client document text`, `SHALL NOT distinguish "does not exist" from
  "access denied"`).

## 3. Rules

1. Numbering is stable. Insert with suffixes (`5a`), never renumber; tasks and
   properties reference these ids.
2. Every requirement has a user story with a real role from the product's
   persona list.
3. Glossary terms are defined once and used verbatim in criteria.
4. Research-derived claims carry an evidence note: the source, its date, and
   whether it is primary or secondary; a prediction is not a requirement.
5. Constraints name the implementation gate they impose ("encryption lands
   before any real PII reaches production").
6. When a requirement conflicts with an authoritative upstream (a validated
   data pipeline, a shipped contract other specs depend on), the requirement is
   corrected, not the upstream; record the correction.
7. The introduction states the one invariant the spec exists to satisfy, when
   there is one.
8. A requirement that is a legal or professional boundary (professional-
   advice limits, privacy law, accessibility law) names the law and the
   mechanical guard, not only the intent.
9. **Every user story names its schema.** In the generative stack the
   schema is what produces the REST routes, the MCP tools, the generated
   types and, once the frontend track (`typescript/12`) ships, the default
   screens (`shared/13` §2a says what generates today), so a story without
   a schema has nothing to generate and nothing to test against. The
   `**Schema:**` line names the entity schema (new, or changed with the
   fields), the view descriptor, or the registered Tier 3 operation the story
   introduces or alters. `none` is allowed only with a reason (pure UI
   behaviour over an existing schema, an operational or documentation story),
   and such a story still cites the existing schema it renders or operates.
   Acceptance criteria about data shape, validation and policy are written
   as schema facts (`required`, enums, formats, `x-owner-field`, `x-*-reason`)
   so the criterion and the generated behaviour cannot drift; the criterion
   cites the field.

## 4. Validation

- Title and user-story blocks are format-validated.
- Each criterion parses as one of the EARS forms.
- Every requirement id is referenced by at least one task after `tasks.md`
  exists; orphan requirements are a finding.
- Cross-spec references name the spec directory and its phase.
- Every requirement has a `**Schema:**` line; a named schema or view file
  exists in the spec's `schemas/` (draft) or the repository's schema
  directory by the time `design.md` is approved; a named operation exists in
  the design's registry table; `none` carries a reason. A story whose
  criteria mention a field absent from its schema is a finding.
