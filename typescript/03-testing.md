# Testing (TypeScript / React)

## 1. Absolute rules

- Never `it.skip`, `describe.skip`, `xit`, `xdescribe`, `test.fixme`,
  `test.todo`, or `test.skip` in Playwright. Never comment out a test or
  assertion. Never `continue-on-error` on a test step except the documented
  non-blocking PR-CI jobs.
- Fix the code, fix the test, or escalate.

## 2. Unit and integration

- Vitest + `@testing-library/react` + `@testing-library/user-event`;
  `{Component}.test.tsx` co-located.
- Domain components: render with props, interactions, validation,
  accessibility. **Every domain component test file includes at least one
  `axe` assertion** (`vitest-axe`/`jest-axe`), covering default and
  interactive states.
- Hooks: test with a mock port implementation (stub adapter), assert state
  transitions, service calls, error handling.
- Adapters: test against MSW, asserting request/response mapping and error
  transformation.
- Data hooks (`useEntity` etc.) and `useAsyncQuery` have their own tests;
  mocks of the API client are memoised (ratchet check
  `unmemoized_apiclient_mocks`).
- Coverage: ≥ 70% overall (schema-driven app) or 100% on new code (classical
  app); enforced locally at Tier 1, reported in CI.

## 3. End to end (Playwright)

- Projects: `api` (headless, `api.*.spec.ts`), `chromium`, `firefox`,
  `webkit`, `mobile-chrome`, `mobile-safari`. Browser projects ignore
  `api.*.spec.ts`. Admin specs are tagged `@admin` and filtered with
  `--grep`/`--grep-invert`.
- **One runner script** (`run-tests.sh -t <suite> -b <browser> -e <env>`)
  loads the env file, checks service health, and maps flags. Never call
  `npx playwright test` with hardcoded project flags.
- **URLs are config, not code.** `test.config.ts` reads `BASE_URL`,
  `API_URL`, `ADMIN_URL` from env and fails fast. No `|| 'http://…'`
  fallbacks in spec files.
- Every spec includes at least one full user journey using
  `test.describe.serial` (register → approve → login → act), not only page
  tests.
- Every new page has an axe-core WCAG 2.1 AA check in its E2E spec.
- `test-map.json` maps source globs to specs for `--changed-only`; an unmapped
  changed file runs everything (exit 2 safety net). Add mappings with every
  new spec or source path.
- Doc specs (`*.doc.spec.ts`, Test2Doc) generate documentation and do not
  replace E2E coverage; a doc-coverage gate asserts each required doc spec
  exists and collects ≥ 1 test.

## 4. CI tiers

| Tier | Trigger | Blocking |
|---|---|---|
| 1 local | before any handoff | lint, types, unit + coverage, component a11y, build, API + chromium E2E, desktop cross-browser before handoff |
| 2 branch CI | every push | all of the above plus Docker builds, integration, sharded E2E |
| 3 PR CI | PR to main/develop | Tier 2 plus accessibility, performance, visual, cross-browser as **non-blocking** signals until mature |
| 4 deploy gate | after deploy to dev | cross-browser (sharded), mobile, a11y audit, API regression — **blocking** before staging |

Promote a non-blocking job to blocking in the same change that records the
baseline it now passes.
