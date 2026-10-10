# Subject–object extraction and domain mapping

How free text, form fields and detected values become **domain objects and
properties** that every consumer (questions, forms, rules, reports, other
systems) can share: extract who-did-what-to-what, resolve mentions to
canonical entities, bind source fields to a unified domain model, converge
the same concept across sources, map outward to external systems and back
again. Source: the entity-mapping, canonical-name registry, unified model,
binding, prefill, synonym-proposal and logic-axis modules of a pipeline
application; generalised.

## 1. Subject–predicate–object extraction

- Reduce an item to the text its author wrote (drop quoted history,
  forwards, signatures, boilerplate; list every cut) before any parsing.
- Extract one **triple per predicate**: `actor (subject)`, `predicate`,
  `objects`, `target (indirect object)`, with flags `negated`, `modal`,
  `question`, `instruction`, and character offsets back into the source.
- Resolve references deterministically from context first: first person =
  the author, second person = the recipient, first person plural = both,
  from the headers; an unresolved pronoun is tagged `guess` and excluded
  from rendered notes while kept in analysis.
- Map predicates to a **closed event-class vocabulary** per profile
  (`04` §9) through verb clusters; a negated agreement is a decline, a
  question or instruction that asks for action is a request; unknown verbs
  are `other` and counted so the lexicon can grow deliberately.
- Measure before trusting: a random sample of triples with a blank
  "correct" column is reviewed and the accuracy rate recorded in the
  analysis manifest. Triples are reading aids until that rate is known.

## 2. Entity resolution and canonical names

- **One resolver** turns mentions (addresses, handles, phone numbers,
  display names, firm domains, product codes) into canonical entity ids;
  nothing else re-implements identity. Keys are normalised the same way
  everywhere (lower-cased addresses plus their domain, phones by trailing
  digits, names by collapsed whitespace).
- A **canonical-name registry** maps the spellings that different sources
  and extractors use for one concept (`ner_person`, `applicant_name`,
  `name` → `person_name`) and normalises before lookup (ordinal suffixes,
  tool prefixes, inner digit runs). Convergence that ignores the registry
  only ever matches identical strings; measure the share of concept groups
  the registry actually drives.
- Unmapped mentions stay `unknown` and are listed as unmapped; they are
  never guessed into a role or an object.

## 3. The unified domain model

- A small set of **domain objects** (party, organization, account, matter
  or project, document, financial item, location, …) each with
  **properties** (name, address, identifier, date, amount, …), **roles**
  where one object kind plays several parts (`party.applicant`,
  `party.respondent`, `account.payer`), and a **type** per property
  (string, date, money, bool, address, reference, list-of).
- **Cardinality is declared per property**: `one` or `many`; a `many`
  property has a row template (list-of a node); a `reference` property binds
  into another object rather than storing within.
- The model is the bridge between sources and systems: for each object and
  property, the mapping to every connected system's field path is recorded
  (`system_mappings`), including "no equivalent", so an integration gap is a
  row, not a surprise.
- The model is **sparse and grows by evidence**: a growth report ranks what
  sources demand it become (object, proposed property, how many sources
  carry it, inferred type, in model or not). Propose, don't force; a person
  reviews and applies.

## 4. Bindings: source field → domain property

Every source document, form, schema or dataset gets a **bindings file**:

```
{ source id, substrate (pdf/docx/xlsx/api), n_fields, n_mapped,
  partition: { bound, explained, unexplained_by_reason },
  bindings: [ { field address (stable URN), field_label, control_name,
                domain_object, domain_property, role (value|label|total|…),
                field_kind (input|computed|attachment|instruction),
                cardinality (one|many), section, side/role qualifiers,
                confidence, reasoning } ],
  worklist: [ unexplained fields with the reason they are not bound ] }
```

- **Accepted bindings and proposals are separate files**; a model or a
  heuristic writes proposals, a person (or a reviewed rule) promotes them.
- Every field is **bound, explained, or on the worklist** with a reason
  (instruction text, decorative, duplicate, out of scope). The partition
  sums to the field count; a build fails when it does not.
- Field identity is a stable address (document id + version + cell or
  control path), never the label text; labels are recorded for humans.
- Manual **overrides** live in one overrides file consulted by the index,
  so a correction survives regeneration. Each override row cites the field
  addresses and item ids that justified it and carries `recorded`; lint marks
  a row stale when a cited source version is superseded; the write is a
  `curate` op in the log (`second-brain/01` §11).

## 5. Indexes, convergence and reverse mapping

- The **mapping index** provides forward lookup (field → object.property
  with confidence), reverse lookup (object.property → every field in every
  source that carries it), per-source listings, and dynamically derived
  paired fields (first/last name, start/end date).
- **Convergence across sources**: when the same `object.property` is bound
  in N sources, it is one domain attribute. This is what lets a value be
  captured once and used everywhere (answer once, fill many), and what
  turns per-source dedup into a cross-source concept map. Conflation of
  distinct roles (`party.name` versus `party.representative.name`) is the bug the
  role qualifier exists to prevent.
- **Reverse mapping (prefill)** takes `object.role.property` keys
  (three-part when roles collapse variants into one object) and emits the
  field values for a target source, with a coverage report of mapped and
  unmapped keys.
- Confidence on a binding drives whether a consumer asks a verification
  question or takes the value on trust; it is calibrated against the review
  sample, never assumed.

## 6. Binding contracts for cross-structure references

Any field whose value must resolve into another structure (a code list, a
tree of regions or units, a schema id, a rule identifier) has a written
**contract**: the namespace the valid values come from, the consumer that
checks them, the meaning of an empty value, and a test. Contracts are
inventoried in one file; a test suite runs them; a reviewer agent reports
holds and breaks with literal example values and the producer responsible.
Untested cross-structure references were the single largest silent-failure
class in the source application (a materialiser produced zero output for a
whole layer because two trees disagreed about where a code lived).

## 7. The logic-axis surface (normative and classificatory text)

For items that carry rules, policies or requirements, per-item
**classification axes** are extracted once and consumed by many:

| Axis | Shape | Re-checkable |
|---|---|---|
| modality (mandatory / discretionary / prohibited), with dual normalisation of negated forms | enum | by judge |
| subject (the actor a norm binds) | enum from the profile | by judge |
| modal character (conduct norm, definition or scope, knowledge state, purpose) | enum | by judge |
| exceptions and priority clauses, temporal constraints, evidentiary markers, value priorities | **verbatim quotes** | by substring test against the source |
| category (primary domain), functional type (sequence-and-gates versus how-a-step-is-done) | enums | by judge, membership not uniqueness |
| applicable domains / scopes | tag set with calibrated threshold | derived, excluded from vet identity |
| condition / action / triggers / factors | structured fields | by schema |

Rules: the axis list is **closed and versioned**; a new axis argues its way
past the table because every version costs a full re-classification and a
re-vet; runtime consumers (a reasoner, a workflow graph, an argument model,
an ontology export) consume axes and are never themselves axes; quote axes
are verbatim so they rest on the text, not on a model's say-so; label-only
changes flow through a classification stage with provenance
(`classification_chain`: version, prompt hash, from → to, operative quote)
and never re-key extraction.

## 8. Synonyms and vocabulary growth

- Proposals for new synonyms, roles or domain terms are mined from the
  corpus with explicit thresholds (minimum count, minimum score, grouping
  distance) and split by kind (actor versus thing, person versus
  organization), written to a proposals file with the packs and parameters
  that produced them.
- A person reviews proposals; accepted terms enter the one vocabulary
  module with a version bump and change-log line; nothing is auto-applied.
- Growth and synonym reports name their population (which sources, which
  thresholds).

## 9. Consumers

Downstream consumers read the domain model and bindings, never raw fields:
question sets generate one question per domain attribute (not per form
field); forms and templates fill from the model through prefill; rules bind
variables to domain properties; external systems are reached through
`system_mappings`; reports and dashboards group by object and role.
Confidence-bearing bindings decide verification questions versus
auto-fill.

## 10. Tests

| Concern | Check |
|---|---|
| extraction | sample accuracy rate recorded; negation and question rules; `guess` excluded from notes |
| resolution | one resolver (AST sweep for a second normaliser); unmapped mentions listed |
| registry | normalisation cases; share of concept groups driven by the registry measured |
| model | every property has a type and cardinality; every object has system mappings or an explicit "no equivalent" |
| bindings | partition sums to field count; proposals never written into accepted bindings; overrides survive regeneration; every override row cites its sources and `recorded`, and a superseded source marks it stale on the next lint |
| convergence | the same `object.property` across N sources resolves to one attribute; role qualifiers prevent conflation |
| prefill | reverse coverage report; round-trip field → model → field is identity for bound fields |
| contracts | every cross-structure reference has a contract row and a test; the reviewer reports literal violations |
| axes | closed list; quote axes pass the substring test; classification chain present on every relabel |
