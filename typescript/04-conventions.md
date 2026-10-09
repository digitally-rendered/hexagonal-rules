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
- Component library: MUI (pin the major; v7 ≠ v5 APIs). Style with `sx` and
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
