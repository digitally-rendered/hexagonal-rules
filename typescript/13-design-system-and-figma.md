# The design system as a schema-driven hexagon, and working with Figma

The design side gets the same treatment as the backend: a small core
(tokens, a component contract, screen specs) that owns the truth, with
Figma, the React renderer and the generator as adapters. Then designers and
agents can change the look of every generated screen (`typescript/12`)
without anyone editing a theme by hand, and a Figma frame can become a
registered override instead of a re-implementation.

## 1. The hexagon

```
core      tokens (design-tokens JSON)          the one source for colour, type, space, radius, motion, elevation
          component contract                   stable keys: schema field type / view part / slot  →  component name + props
          screen specs                         which generated screen, which overrides, which states, per role
ports     TokenSourcePort                      read/write tokens in a design tool
          DesignFilePort                       read frames, components and variants from a design file
          CodeMappingPort                      bind a design component to a code component (Code Connect or equivalent)
          RendererThemePort                    produce a renderer theme from tokens
adapters  Figma variables, Figma components,   design tool side
          Figma Code Connect, the Figma MCP server
          MUI CSS-variables theme, Storybook   code side
```

Dependency rule: the core knows nothing of Figma or MUI. Token names,
component keys and screen specs are vendor-neutral; adapters translate.
Enforced by an import fitness test over `design/core/**`.

## 2. Tokens are the contract

- Tokens live in the repository as design-tokens JSON (the community-group
  format): `color.*`, `font.*`, `space.*`, `radius.*`, `shadow.*`,
  `motion.*`, with **semantic** aliases (`color.surface.default`,
  `color.text.danger`) over primitives. Components reference semantic
  tokens only; a primitive in a component is a lint failure.
- Figma variables and the renderer theme are both **generated from the
  tokens**; neither is edited by hand. The Figma adapter pushes and pulls
  variables through the tool's variables interface or a plugin that speaks
  the same JSON; the renderer adapter emits the MUI theme in
  CSS-variables mode so a token change is a CSS variable change at runtime.
- Modes (light, dark, high-contrast, density) are token sets, not
  components. Every semantic token has a value in every mode; a missing
  value fails the build.
- A token change is a commit with a visual diff (Storybook or screenshot
  tests) and, when it moves a semantic alias, a note in the design decisions.

## 3. The component contract maps schema to design

This is what makes the design system schema-driven: the same keys the
generator uses (`typescript/12` §3) name the design components.

| Schema input | Component key | Figma component | React (generated default) |
|---|---|---|---|
| `string` | `field.text` | Text field | text input |
| `string` + `enum` | `field.select` | Select | select or radio by option count (`x-ui-widget`) |
| `string` + `format: date-time` | `field.datetime` | Date picker | date-time picker |
| `number`, `integer` | `field.number` | Number field | number input with min, max, step from the schema |
| `boolean` | `field.boolean` | Switch or Checkbox | switch (`x-ui-widget: checkbox` to override) |
| `array` of primitives | `field.tags` | Chip input | chip input |
| `array` of objects, `object` | `field.subform` | Card group | nested form section |
| `$ref` to another schema | `field.reference` | Entity picker | async picker over the referenced list hook |
| `x-view` columns | `list.column.<type>` | Table cell variants | grid column renderers |
| operation with capability tag | `action.<kind>` | Button variants | action button, hidden without capability |
| `x-*-reason`, description | `help.inline` | Help text | tooltip and helper text |
| states | `state.empty`, `state.loading`, `state.error`, `state.forbidden` | State frames | shared primitives (`typescript/05` §9) |

Rules: every component key has exactly one Figma component (with variants
for state and mode) and one default React renderer; adding a key to one
side without the other fails the parity audit; a Figma component without a
code binding is a design-only draft and is tagged so.

## 4. Figma as an adapter, and the Figma MCP server as a build tool

- **Code Connect** (or an equivalent mapping) binds each Figma component to
  its React component and props. The mapping file is generated from the
  component contract, so renaming a key renames both sides.
- **The design tool's MCP server** is a build-brain tool
  (`second-brain/06` §3): the coding agent reads a selected frame, its
  variables and its component instances, and produces a registered
  override, never a free-hand screen. It is registered read-only in the
  project MCP config (`templates/mcp-project.json` pattern); it never runs
  in production and never sees record data.
- Design files are a **source**, not a store of truth for code: a frame
  that disagrees with the tokens or the component contract is a design
  change request, recorded as a contradiction (`shared/07` §3), not a
  reason to hard-code a value.
- Screens designed in Figma are built as overrides at the narrowest
  granularity that reproduces them; a frame that is only a restyled default
  becomes a token or variant change, not an override.

## 5. Skills

Each follows the skill contract (`shared/11` §5): declared inputs, outputs,
checks and a report; no bypass flags.

| Skill | Inputs | Does | Checks before it finishes |
|---|---|---|---|
| `design/sync-tokens` | tokens JSON, design file id | pushes or pulls variables through the token port; regenerates the renderer theme | every semantic token has every mode; Figma variables equal the JSON; visual diff produced |
| `design/map-components` | component contract, design file | generates the Code Connect mapping and the Storybook stories per key | every key has one Figma component and one renderer; orphan components listed |
| `design/screen-override` | a frame id, the target schema and operation | reads the frame via the MCP server, chooses the narrowest override granularity, writes the override using generated hooks and types, registers it | fitness tests pass; no primitive tokens; axe clean; `features/` is the only directory touched |
| `design/parity-audit` | repository | compares schema field types, component keys, Figma components, renderers and tokens | reports gaps in each direction; fails on an unmapped key or a hand-edited theme |
| `design/visual-regression` | Storybook build | screenshots every component key in every mode and every generated screen state | diff against baseline; new baselines need a reason in the commit |

## 6. Tests

| Concern | Check |
|---|---|
| design hexagon | import fitness test: `design/core/**` imports no Figma or renderer package |
| tokens | schema validation of the tokens JSON; every semantic token has every mode; no primitive token referenced from a component |
| generated theme | theme file is regenerated and diffed in CI like any generated file; a hand edit fails `codegen:check` |
| contract parity | every component key ↔ one Figma component ↔ one renderer; Code Connect mapping regenerated from the contract |
| overrides from design | an override produced by the skill passes the fitness tests and the ratchet, and uses only generated hooks and types |
| visual | Storybook screenshot baselines per key, mode and state; generated screens included |
| no data in design tools | the design MCP server is read-only, project-scoped and absent from production config; fixtures only, never records |
