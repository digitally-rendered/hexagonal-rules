# The generated agent surface: one schema, a human UI and a working MCP server

The point of the generative stack is not a REST API with a UI bolted on. It
is that one schema and one set of use cases generate **two surfaces** for the
same feature: a human surface (generated types and validators, consumed
through the shared data hooks, under hand-written screens) and an agent surface (an MCP server whose tools, resources and prompts an agent
can call), so that a person and an agent can work on the same records
through the same core with the same authorization and the same audit. A
feature is not done until both surfaces exist and are tested, and the
agent surface actually runs against a real client.

Sources: the frameworks' `mcp` channel and `RequestContext.channel`
([slip-stream](https://github.com/digitally-rendered/slip-stream),
[stellar-drive](https://github.com/digitally-rendered/stellar-drive),
[Syntact](https://github.com/digitally-rendered/Syntact)); the consumer
verb contracts of `shared/09` §11; the privacy layering of `shared/08`.

## 1. Two MCP servers, two brains

| Server | Serves | Brain (`shared/14`) | Tools |
|---|---|---|---|
| **developer MCP** (framework CLI `mcp`) | the coding agent while building | build | schema list/validate/diff, query the registry, run codegen, read the route table, run the dev loop, impact of a schema change |
| **application MCP** (generated per application) | the application's own agent and any external agent acting for a principal | operation | one tool set per schema and per Tier 3 use case, resources over records and views, prompts per workflow |

The developer MCP never runs in production; the application MCP never
exposes build state. Both are driving adapters: they build a
`RequestContext` with `channel = mcp` and call the one executor, exactly as
REST and the UI do. Nothing in either reaches persistence directly. Check:
§6 "no build leakage"; the production config contains no developer-server
entry; the fitness test finds no persistence import under either server.

## 2. What is generated, from what

| Schema input | REST, SDK (generated) | Human UI (generated types and validators, read through the shared data hooks; screens hand-written, see §2a) | Agent surface (generated) |
|---|---|---|---|
| entity schema | CRUD routes, bulk, history (where the repository port exposes it), typed client | `types.ts`, `schemas.ts` (validators), read through the shared `useEntity`/`useEntityList` hooks; list, detail and forms written over them | `<entity>_get`, `<entity>_list`, `<entity>_create`, `<entity>_update`, `<entity>_delete`, `<entity>_history` where the repository port exposes history; a resource `<entity>://{id}` and `<entity>://` templates |
| view schema | read route | `views.ts` descriptor, read through the shared `useView` hook; the table itself written over them | `<view>_query` with the view's filters as typed arguments; a resource per view |
| Tier 3 use case (registered operation) | custom route; `apiTypes.ts` from OpenAPI | action button or wizard, hand-written over the generated API types | one tool per use case, name from the registry; `simulate_<use_case>` sibling for mutations |
| `x-*` reasons on fields | OpenAPI descriptions | available to form help text through the generated schema | tool and argument descriptions: the agent reads the same reasons the human does |
| `required`, enums, formats | validation | zod constraints in `schemas.ts` | the tool's input JSON Schema is the Create/Update schema itself; no second hand-written schema |
| errors table (`shared/01`) | status codes | error presentation | typed MCP errors with the same codes; `isError` results carry the domain error, never a stack |
| workflows (operating skills, `shared/11`; the spec system's task waves, README) | none | guided pages, hand-written | MCP prompts: one per workflow, parameterised, pointing at the tools it uses |
| events (`shared/01`) | webhooks | live updates, hand-written subscriptions | notifications or a `<entity>_changes` resource with a cursor |

### 2a. What generates today, per stack, and where the UI stops

| Stack | Backend from schema | SDK | MCP | UI |
|---|---|---|---|---|
| Python ([slip-stream](https://github.com/digitally-rendered/slip-stream)) | models, routers, services, repositories | generated typed client | developer stdio server module with tests and benchmarks; application server: design | via star-board from the emitted OpenAPI document once the backend carries the §6a extensions (`shared/02`); the schema-driven application's own script emits types, validators and view descriptors |
| Go ([stellar-drive](https://github.com/digitally-rendered/stellar-drive)) | structs, repositories, services, handlers, GraphQL, overrides, OpenAPI | generated client | developer stdio server; application server: design | via star-board from the emitted OpenAPI document once the §6a extensions are emitted |
| TypeScript ([Syntact](https://github.com/digitally-rendered/Syntact), in flight) | planned at parity with the Go port | planned | planned (`mcp` CLI and package) | via star-board from the emitted OpenAPI document |
| TypeScript/React ([star-board](https://github.com/digitally-rendered/-star-board-)) | consumes the document | generated typed client | consumes the application MCP tool list for parity and the agent affordance | default screens, action hooks, routes, registry, agent panel from the document (`typescript/12`) |

So the generative stack today is **backend + SDK + a developer MCP from one
schema**, plus **the human UI from the emitted document** through star-board;
the application MCP server of §1 is still a design in every backend, so the
parity suite runs against a tool list fixture until it ships. A backend's UI
is generated the moment its document carries the `shared/02` §6a extensions;
`fixtures/petstore.json` in star-board is the hand-authored reference until
then. Rules that follow from this:

- **Say which it is.** A rule or spec that calls the UI "generated" means
  the generated layer, never pages or forms, until a renderer exists.
- **The agent surface is the primary generated surface for a feature.** It
  is complete from the schema with no hand-written step, so it is the
  first surface a feature has, and the parity test runs against it before
  any screen exists. A feature usable by an agent and not yet by a human is
  an honest intermediate state; the reverse is not allowed.
- **The target** is a schema-form renderer that turns the Create/Update
  schema, the view descriptor and the `x-*` reasons into default list,
  detail and form screens, with hand-written screens as overrides preserved
  on re-run, exactly as backend override stubs are. That target is
  specified as the **frontend track** with its design system (designs in
  the TypeScript folder; README lists them); it is a design, not a fact
  about the current frameworks; until it ships, the drift check
  (`shared/02` §1) covers the generated types, the SDK and, where a stack
  generates them, the MCP artifacts; it never covers the shared data hooks
  or screens.
- **Status of the agent-surface rules.** The `simulate_`/`why_` siblings,
  the streamable HTTP transport, the client fixture and the parity suite
  (§2, §5, §6) are requirements on every stack's application server. As of
  2026-10-09 no shipped server implements them (the Python developer server
  is stdio-only and has no siblings). Language files state them as "MUST
  have (`shared/13` §2)", never as present-tense facts, until they cite the
  framework path that implements them.

Rules:

- **No hand-written tool schemas.** The tool input schema is derived from
  the registry, so a schema change regenerates REST, UI types and tools in
  one `generate` run; the drift check (`shared/02` §1) fails if any surface
  drifts.
- **Tool names are derived and stable**: `<schema>_<operation>` and the
  registered use-case name; renames go through the schema registry so all
  three surfaces move together.
- **Every reading tool has an explain sibling, every mutating tool a
  simulate sibling** (`shared/09` §11): agents reason before acting and can
  show their reasoning to the human.
- **Descriptions are the product's own words.** The `x-*-reason` text, the
  field titles and the use-case docstrings are the agent's documentation;
  if an agent misuses a tool, fix the schema's description, not the agent's
  prompt.
- **Parity is tested.** For each registered operation, a test asserts that
  REST, UI generated types and MCP tool all exist, carry the same version,
  and reject the same invalid payloads.

## 3. The agent is a principal

- The MCP connection authenticates a **principal** and, when the agent acts
  for a user, an **on-behalf-of delegation** (`shared/08` L5). The tool call
  carries both in the `RequestContext`; the executor's guards, ownership
  scoping and ReBAC checks run unchanged. Check: §6 "scoped tool list" and
  "OBO audit"; a tool call and the REST call for the same principal and
  record return the same status.
- An agent sees what its principal may see and does what its principal may
  do; a tool list is filtered by capability so unavailable actions are not
  advertised. The filtered list is the same source as the UI's hidden
  buttons. Check: §6 "scoped tool list".
- Every tool call is an audit event with actor type `agent`, the delegating
  user, the tool name, the inputs hash, and the model and prompt version
  when known (`shared/10` §5). Simulations are logged as simulations.
  Check: §6 "OBO audit"; the M5 live-client test asserts one audit row per
  call with the simulate flag set on the simulate call.
- Rate limits, budgets and dangerous-action confirmation are policy in the
  executor, not in the MCP adapter, so they apply to REST and UI as well.
  Check: a fitness test finds no rate-limit, budget or confirmation logic
  under the MCP adapter package.
- Secrets never cross the surface: tool results are projected through the
  same field-level projection and classification filter as responses.
  Check: a projection test calls a read tool and the matching REST route for
  a document with a classified field and asserts the two bodies are equal.

## 4. Human–agent interaction patterns

The generated surfaces let the same feature be used four ways; the schema
and use cases do not change between them.

| Pattern | Human | Agent | Mechanism |
|---|---|---|---|
| human drives, agent assists | uses the UI | proposes via tools in simulate mode; human applies | the UI shows the agent's proposal and its `why_` rationale next to the form |
| agent drives, human approves | approves in the UI | calls mutating tools that require confirmation | an approval record in the workflow; the tool returns `pending_approval` and a resource to watch |
| agent operates within bounds | reviews the audit and exceptions | calls tools autonomously under a budget and allowlist | per-principal capability set and spend limits in policy |
| agent to agent | none, except audit | an external agent calls the application MCP with its own principal | same server, same guards; no special path |

Rules, each with its check:

- A human can always see what an agent did and why, from the audit and the
  `why_` rationale. Check: the M5 live-client test reads back the audit row
  and the rationale for every call in the conversation.
- A human can always do by hand through the UI what an agent did. Check:
  the parity test (§6): every tool maps to an operation that has a REST
  route and a UI action or screen.
- An agent never has a capability a human principal could not be granted.
  Check: a test over every agent principal asserts its capability set is a
  subset of its delegating user's (or, with no delegation, of some human
  role's) capability set; a capability present only on an agent fails.

## 5. In the vertical slice

The agent surface is a phase of the slice (`shared/07`), built after the
backend and before or alongside the frontend, with its own tests:

| Step | What you write | Test before moving on |
|---|---|---|
| M1 generate | nothing: `generate` emits the tool set, resources and prompts from the registry | the drift check (`shared/02` §1) clean; tool count equals registered operations × surfaces expected |
| M2 register | the application MCP server mounts the generated tools; custom tools registered before generated ones so they cannot be shadowed | server starts; `tools/list` returns the filtered set for a test principal |
| M3 parity | nothing new | the parity test: REST, UI types and tool agree on schema version and reject the same invalid payloads |
| M4 authorization | nothing new | tool calls with a scoped principal see only their rows; a delegated call is audited with both actors; a denied capability is absent from `tools/list` and rejected on call |
| M5 live client | an MCP client fixture (the official SDK client or the framework's test client) | an end-to-end conversation: list tools → call a read tool → simulate a mutation → apply it → read it back → see it in the UI's data hooks |
| M6 agent eval | a golden conversation per workflow prompt | an eval with a real model under the harness (`shared/10`): the agent completes the workflow using only the generated tools; judged against a rubric; failures become description fixes |

The definition of done adds: application MCP generated, parity green, a
live client test per feature, and an agent eval per workflow prompt.

## 6. Tests

| Concern | Check |
|---|---|
| drift | the drift check (`shared/02` §1) covers tools, resources and prompts in the stack that generates them |
| parity | one test per registered operation across REST, UI types, MCP, and generated screens once the frontend track is in use (the track's own parity test) |
| no hand-written tool schema | lint: tool input schemas reference registry schemas by id |
| scoped tool list | `tools/list` differs by principal exactly as the UI's capability set does |
| OBO audit | delegated calls carry both actors; a missing delegation fails closed |
| simulate before mutate | every mutating tool has a simulate sibling; the simulate tool has no side effects (repository call count is zero) |
| live client | the server speaks to a real MCP client in CI, stdio and streamable HTTP |
| agent completes the workflow | a model-driven eval per prompt with a coverage floor; self-reported success never gates (`shared/06`) |
| no build leakage | the application MCP exposes no registry-admin, codegen or repo tools |
