# Second-brain project design

Rules for designing a knowledge and evidence record (a "second brain") the
way a private evidence-management workspace is built; domain-neutral, with
the dispute file as one profile: read-only evidence collection, a fixed
case model, audience-scoped generated vaults, a verified fact registry, and a
recurring review cycle, all driven by code with AI as proposer, not author.

| File | Contents |
|---|---|
| `01-project-design.md` | the three-folder layout, storage tiers, fixed schema, generated vs owned content, classification, facts and gaps, review cycle, handoff, AI rules |
| `02-requirements-and-design.md` | how research and business inputs, facts and decisions feed the spec system |
| `03-evidence-lifecycle.md` | the item-level lifecycle (ingest → notarize → store → extract → classify → index → search → review → tag → produce) and defensibility: custody chains, manifests, exhibits, what proves what, tracking of inputs, tools and access |
| `04-topics-issues-and-relationships.md` | the content graph: node and edge types with cardinality, temporal and logical tags, topics and episodes, curation, counting and reasoning across the set, per-domain profiles |
| `05-domain-mapping.md` | subject–predicate–object extraction, entity resolution and canonical names, the unified domain model, bindings and contracts, convergence and reverse mapping, logic axes, vocabulary growth |
| `06-design-brain-and-system-brain.md` | the design brain (intent, specs, decisions, learnings) versus the system brain (record, model, procedures, runs, indexes, session memory): memory taxonomy for an agentic system, session handoff, the loop between them, agent read/write policy |

Related: `shared/08-data-privacy-layering.md` (audience, privilege, storage
tiers) and `shared/06-evals-and-verification.md` (verify before use, count
the population).
