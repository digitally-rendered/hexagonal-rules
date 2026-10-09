# Conventions (TypeScript / React)

- TypeScript strict. No `any` escapes without a comment.
- Functional components and hooks only; no class components.
- One responsibility per file: a component, a hook, a port, an adapter, a
  types module. Small files make granular, accurate changes (human and agent).
- Decompose large components into focused children.
- `index.ts` per directory as the module's public API; import from the
  directory.
- Lazy routes (`React.lazy` + dynamic `import()`), one `Suspense` boundary per
  route group.
- Component library: MUI (pin the major; v7 ≠ v5 APIs), reached by generated
  code only through the component registry (`typescript/12` §3–4); theme in
  CSS-variables mode generated from tokens (`typescript/13`). Style with `sx` and
  utility classes; no `makeStyles`/`styled` for layout. Never mix two
  component libraries inside one component; shadcn-style primitives live under
  `domain/components/ui/`.
- Forms: React Hook Form + Zod; Zod schemas come from the generated layer when
  the backend schema exists.
- `data-testid` on every interactive element.
- Naming: `PascalCase.tsx` components, `camelCase.ts` utilities/hooks
  (`useX.ts`), `I<Name>Service.ts` ports, `<Name>ServiceAdapter.ts` adapters,
  `<Name>Page.tsx` pages.
- Lint/format: ESLint 9 + Prettier; `npx tsc -b` must be clean; both run in
  pre-commit and CI.
- Env: `VITE_*` for client config; demo/persona switches gated by env, never
  hardcoded.

## Backend (Node) conventions

- ESM only; `moduleResolution: NodeNext`; strict flags including
  `exactOptionalPropertyTypes`, `noUncheckedIndexedAccess`,
  `verbatimModuleSyntax`; project references; one `index.ts` per package
  with an `exports` map carrying `types`.
- No default exports in core packages; named exports only.
- Naming: `<name>.repository.ts` exporting `<Pascal>Repository`,
  `<name>.service.ts`, `<name>.handlers.ts`; ports are interfaces named
  for the capability; adapters carry the technology.
- Errors wrap with `cause`; typed error classes with a closed `code` union;
  never throw strings.
- `AbortSignal` is first-class on every async boundary (requests, plugins,
  model calls).
- Structured logging (pino) through a logger port; never `console` in
  library code.
- Env overrides use one framework prefix; config is validated once at
  startup by a schema the framework owns.
- Dynamic `import()` only in composition roots and optional-dependency
  probes, each commented.
- Tooling: ESLint flat config with type-checked rules, boundaries plugin,
  Prettier, knip for unused exports, dependency-cruiser, changesets for
  releases, husky + lint-staged for pre-commit.
