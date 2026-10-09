# UI platform rules (TypeScript / React)

Cross-cutting frontend concerns found in the specs and code that the layer
rules do not state: dependency injection, error presentation,
accessibility, regulated wording, roles, mobile, i18n, and embedded
micro-frontends. Sources: the frontends and admin portals of the application
sources, an embedded micro-frontend, and the mobile/PWA and onboarding specs.

## 1. Services provider (dependency injection)

- One `ServiceFactory` builds every secondary adapter from a shared config
  (API base URL, websocket config, retry and cache settings). One
  `ServiceProvider` puts the instances in context. `useServices()` (and
  per-service hooks `useCaseService()` etc.) are the only way application
  hooks obtain a port implementation; a hook that constructs an adapter is a
  violation.
- Registering a new adapter means: port interface → adapter → factory entry
  → provider type → hook. The verification checklist for a frontend handoff
  includes "services registered in the factory and provider".
- Tests render under a provider with stub adapters.

## 2. Errors

- Adapters translate transport failures into a typed hierarchy (`ApiError`
  with status, `NetworkError`, `ValidationError` with field errors,
  `AuthenticationError`, `AuthorizationError`, `NotFoundError`), serializable
  for logging.
- **Raw backend text never reaches the user.** The shared query hook maps any
  error to a caller-supplied friendly message; pages render that message. A
  status string like "Internal Server Error" in the UI is the bug class this
  rule exists for.
- Handled failures do not `console.error`; the E2E base fixture fails any
  test that observes an unexpected console error.
- Designs carry a frontend error table: 401 → redirect to login; 403 →
  "insufficient permissions" without redirect; 404 → not-found message in the
  panel; 500 → banner with retry; timeout → toast and auto-retry; empty →
  empty state, never a blank screen; missing chart data → placeholder.
- Hooks return `{ data, loading, error }`; pages check loading, then error,
  then render.

## 3. Accessibility (mandatory)

- WCAG 2.1 AA is a legal requirement under accessibility law where the
  product operates:
  every domain component test includes an axe assertion; every page E2E
  includes an axe-core WCAG 2.1 AA check; a skip-to-content link, keyboard
  navigation, visible focus, and labelled interactive elements are baseline.
- Plain language for non-expert users (about grade 8), tooltips for domain
  terms, and an "I don't know this yet" option on onboarding fields.
- Loading states for every async operation; real-time form validation with
  clear messages; actionable error guidance.

## 4. Regulated wording and guardrails

- Every user-facing surface that reflects regulated content (legal, medical,
  financial) carries the "information, not advice" disclaimer, loaded from a
  professionally reviewed disclaimers file and stamped by the loader, not
  typed into components.
- Results use descriptive, non-evaluative labels ("fewer / several / many
  considerations") with neutral colours, never red/amber/green verdicts;
  exact wording is a requirement and is tested verbatim.
- Any AI-generated regulated content shown to a consumer is verification-shaped
  and human-reviewed; the guard is mechanical (a gate in the flow), not a
  policy note.
- Consent precedes collection: the consent gate is a server-side precondition
  the UI reflects (fields disabled until an active consent record exists),
  never a UI-only checkbox.

## 5. Roles and auth

- Route guards and role checks compare **backend enum values**
  (`end_user`, `professional`, `admin`), never display names. Mapping
  display names for presentation is a separate, presentation-only table.
  Mixing the two produced guards that passed in the UI and failed on the API.
- Legacy role slugs are mapped in one place with a comment naming them
  legacy; new code uses backend spellings only.
- Tokens are injected by the adapter interceptor; components never read
  tokens. A 401 clears the session and redirects once, in the interceptor.
- Demo/persona switching is gated by an env flag and lives in one context.

## 6. Mobile and PWA (cross-cutting from the first user-facing phase)

- Breakpoints: < 768 single column; 768–1024 two columns where useful; >
  1024 desktop. No horizontal page scroll at any width.
- Touch targets ≥ 44×44 CSS px with ≥ 8 px spacing; full-width mobile form
  fields; correct `inputmode`/`type` for mobile keyboards; sticky submit on
  long forms; tables with more than three columns use a responsive pattern.
- Sidebar collapses to a hamburger; primary actions in a bottom bar; scroll
  position preserved on back; compact back button replaces breadcrumbs.
- PWA: valid manifest, service worker for assets, standalone launch, branded
  offline page that does not attempt data loads.
- Mobile viewport E2E runs in the deploy gate; mobile is enforced on every
  new page, not retrofitted.

## 7. Internationalisation

- User-facing strings are extracted; EN and FR are first-class where the
  market requires it; regulated wording is translated by the same reviewed
  source as the primary-language disclaimers, not ad hoc.

## 8. Embedded micro-frontends

- An app embedded in a host (e.g. a partner product's iframe) is a
  **separate entry point and build** with its own `main.tsx` and Vite config,
  served from its own path, themed to the host.
- Communication with the host goes through one hook (`useHost`) wrapping
  `postMessage`; the host's context (the selected record) drives which panel
  renders. The embedded app reuses the same ports and adapters as the main
  app; it never reaches the backend by a second path.
- Panels are domain components; the embed app is the primary adapter.

## 9. Shared UI primitives

- `EmptyState`, `UnsavedChangesDialog` (with `useUnsavedChanges`),
  `SkipToContent`, `HelpCenter`, a notification bell fed by the notification
  domain, and session-timeout handling (`useSessionTimeout`) are shared
  components and hooks; pages do not re-implement them.
- Long-running work is surfaced through a progress stream hook
  (`useProgressStream` over SSE) that is ownership-scoped on the server, with
  queued / running / review-required / failed / stale states and an
  authorized retry action.
- Multi-case users get a selected-case context and a switcher; pages never
  assume `cases[0]`.

## 10. Admin portal

- The admin app is a second hexagonal frontend with the same four layers,
  its own port (`I<Admin>Service`) and generated adapter, its own tests (unit
  with axe, `@admin`-tagged E2E), and it shows record **metadata** by default;
  record contents require an owner-approved grant surfaced in the UI.
