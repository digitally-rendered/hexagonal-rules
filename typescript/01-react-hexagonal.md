# React hexagonal architecture

## 1. Layers

```
src/
├── domain/
│   ├── components/     pure UI ("dumb" components) — the entities/value objects of the UI
│   └── utils/          pure functions
├── application/
│   ├── hooks/          use cases: state + orchestration through ports
│   └── context/        app-level state (selected-record context, services provider)
├── ports/              TypeScript interfaces only (IUserService, I<Entity>Service, …)
├── adapters/
│   ├── primary/        pages / container components; routing; composition
│   └── secondary/      service implementations (HTTP, storage, websocket)
├── infrastructure/api/ shared HTTP client
├── generated/          codegen output (see 02-generated-layer.md); under the frontend track (12):
│   ├── domain/         generated default components (domain layer rules apply)
│   ├── application/    generated typed action hooks (application layer rules apply)
│   ├── adapters/       generated typed client (secondary adapter rules apply)
│   └── registry.ts     the component registry: the port between generator and app
└── features/<schema>/  registered overrides (12 §3): components/ obey domain rules,
    ├── components/     hooks/ obey application rules; nothing here fetches or
    ├── hooks/          declares a shape the generated layer already has
    └── index.ts        registerComponent(...) calls only
```

The fitness test classifies `generated/*` and `features/<schema>/*` by their
sub-folder, so the same import rules apply to generated and override code.

Path aliases `@domain/`, `@application/`, `@ports/`, `@adapters/` are used for
every cross-layer import; never relative paths across layers.

Import rules mirror the backend: `domain` imports nothing from
`application`/`ports`/`adapters`; `application` imports `domain` and
`ports`; `adapters` import everything; `ports` import only domain types.
Enforce with an ESLint `no-restricted-imports` or boundaries rule.

## 2. Domain components

- MUST NOT fetch, call services, read context that fetches, or have side
  effects. All data and callbacks arrive as props. Local state only
  (form state, open/closed). Check: the AST fitness test over
  `domain/components/**` fails on an import of `fetch`, `axios`, the API
  client, the services context or any `adapters/` path.
- Validation is client-side and expressed in props/Zod; errors are rendered
  from props.
- Highly reusable; styled with the component library (`sx`) plus utility
  classes for layout.
- Every interactive element carries a `data-testid`.

## 3. Application hooks

- One hook per business capability (`useOrderManagement`, `useOnboardingFlow`,
  `useNegotiation`). It returns state and the actions on that state.
- MUST NOT call `fetch`/`axios` directly. It calls a **port** obtained from the
  services context (`useServices()`) or passed as a parameter. Check: the
  same fitness test over `application/hooks/**` fails on a direct HTTP
  import; the drift ratchet gates `apiclient_in_deps`.
- Depend on primitive request parameters in effect/callback dependency arrays,
  never on the client object.
- Hand-rolled `[data, loading, error]` trios around a fetch are Tier 2
  boilerplate; use the shared data hooks (`02-generated-layer.md`) wherever
  the backend surface is schema-driven.

## 4. Ports

- `ports/I<Capability>Service.ts`: a TypeScript interface using domain models
  in its signatures. No implementation, no axios types.
- Primary ports are implicit: the props of the page that uses the hook.
- A port is small and capability-shaped; split rather than grow.

## 5. Secondary adapters

- `adapters/secondary/<Capability>ServiceAdapter.ts` implements the port.
- Owns: base URL, auth header injection, retry with backoff, TTL cache for
  read-heavy calls, request/response mapping, and translation of transport
  errors into a typed `ApiError` hierarchy (`NetworkError`,
  `ValidationError`, `AuthError`).
- A stub adapter per port for hook tests.
- Case conversion between `snake_case` and `camelCase` happens here (or in the
  generated mapping layer), never in components or hooks.

## 6. Primary adapters (pages)

- Compose hooks and domain components; handle routing, layout, navigation,
  loading/error presentation.
- Obtain services from a `ServiceProvider` (`ServiceFactory` builds every
  adapter once with shared config) rather than instantiating adapters inline.
- Lazy-load routes with `React.lazy` + `Suspense`.

## 7. Data flow

```
user action → page → hook → port → adapter → HTTP → backend controller
            ← page ← hook ← port ← adapter ← mapped domain model
```

## 8. State management

- React Context + services provider; no Redux/Zustand unless a measured need.
- Each hook owns its loading/error state (or delegates to the shared data
  hooks). Cross-page selection lives in `application/context`.

## 9. Auth

- Auth provider wraps the app; a dedicated hook maps identity-provider roles to
  app roles; tokens are injected by the adapter's interceptor, never read in
  components. Role-based routing via a `ProtectedRoute`.
- Persona switching in demo mode is a context concern gated by an env flag.

## 10. When creating a feature

domain component + application hook + port interface + secondary adapter (+
stub) + page + tests for each. Never a file outside its layer.
