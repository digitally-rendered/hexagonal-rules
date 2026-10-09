# Spec system: steering, requirements, design, tasks, sequencing

Generalised from the spec folders of the application sources, plus the
workflows, state files, hooks and the spec-refinement skill that drive them.
The folder name and refinement tool in use (currently Kiro) are
implementation details; the schemas below are tool-neutral. This is how a feature goes
from research to an executable, wave-sequenced task list, and how the
documents stay honest against shipped code.

| File | Contents |
|---|---|
| `01-spec-system.md` | the layout, the lifecycle, who writes what, hooks, and the verification stack |
| `02-requirements-schema.md` | `requirements.md`: EARS acceptance criteria, glossary, constraints, amendments |
| `03-design-schema.md` | `design.md`: decisions, hex-layer components, data models, errors, correctness properties, testing strategy |
| `04-tasks-and-waves-schema.md` | `tasks.md`: task grammar, requirement back-references, checkpoints, dependency graph and the wave JSON |
| `05-sequencing-and-state.md` | `MASTER_SEQUENCING.md`, the remediation tracker, the handoff JSON, state files, steering docs, team definitions |

The second-brain extension that feeds this system (research and business
inputs, evidence quality, facts and decisions as records) is in
`second-brain/02-requirements-and-design.md`.
