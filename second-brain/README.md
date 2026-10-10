# Second-brain project design

Rules for designing a knowledge and evidence record (a "second brain") the
way a private evidence-management workspace is built; domain-neutral, with
the dispute file as one profile: read-only evidence collection, a fixed
record model, a compiled wiki, audience-scoped generated vaults, a verified
fact registry, one log, and a recurring review cycle, all driven by code
with AI as proposer and the human as editor, not author.

| File | Contents |
|---|---|
| `01-project-design.md` | the three-folder layout, storage tiers, fixed schema, generated vs compiled vs owned content, classification, facts and gaps (the verdict enum), search and filing answers, review cycle with lint, handoff, AI rules and the one `log.md` |
| `03-evidence-lifecycle.md` | the item-level lifecycle (ingest → notarize → store → extract → classify → index → search → review → tag → produce) and defensibility: custody chains, manifests, produced artifacts, what proves what, tracking of inputs, tools and access; profiles and the minimum profile |
| `04-topics-issues-and-relationships.md` | the content graph: node and edge types with cardinality, temporal and logical tags, topics and episodes, curation, counting and reasoning across the set, per-profile vocabularies |
| `05-domain-mapping.md` | subject–predicate–object extraction, entity resolution and canonical names, the unified domain model, bindings and contracts, convergence and reverse mapping, logic axes, vocabulary growth |

How evidence-graded inputs feed the spec system is `specs/06`; the design,
build and operation brains of an agentic project are `shared/14`.

Related: `shared/08-data-privacy-layering.md` (audience, privilege, storage
tiers, the `curator` and `editor` roles), `shared/06-evals-and-verification.md`
(verify before use, count the population) and `shared/11` §1a (the
`knowledge-maintenance` skill).
