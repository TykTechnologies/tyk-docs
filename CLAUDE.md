# Rules for AI Assistant

## Auto-generated files

The following files and directories are auto-generated from source code in other repositories. **DO NOT EDIT THEM DIRECTLY IN THIS REPOSITORY.**

If you need to make changes to the content of these files, you must create a pull request against the appropriate source code repository.

### Swagger API Documentation

All files under `swagger/` are auto-generated from source code repositories and must not be edited directly.

### Environment Variable and Configuration Pages

The following pages are auto-generated:

- `tyk-oss-gateway/configuration.mdx`
- `tyk-dashboard/configuration.mdx`
- `tyk-pump/tyk-pump-configuration/tyk-pump-environment-variables.mdx`
- `tyk-multi-data-centre/mdcb-configuration-options.mdx`
- `tyk-configuration-reference/tyk-identity-broker-configuration.mdx`

The above pages can be edited, but they reference snippets which are imported from other files. These imported snippets cannot be edited directly:

- `snippets/gateway-config.mdx`
- `snippets/dashboard-config.mdx`
- `snippets/pump-config.mdx`
- `snippets/mdcb-config.mdx`
- `snippets/env-type-mapping.mdx`

### Tyk OAS API Reference

The Tyk OAS API reference page at `api-management/gateway-config-tyk-oas.mdx` imports `x-tyk-gateway` content from `/snippets/x-tyk-gateway.mdx`, which is auto-generated and must not be edited directly.

### MDX-Breaking Characters in Synced Content

The auto-sync pipeline (Go doc-comments in `TykTechnologies/tyk` and other component repos, pulled into `snippets/gateway-config.mdx`, `snippets/x-tyk-gateway.mdx`, and the other auto-generated files above) can introduce literal `{...}` or `<...>` text that MDX parses as a JS expression or an unclosed HTML/JSX tag, breaking the build (`Could not parse expression with acorn`, `Expected a closing tag for <name>`). This happens even when the source Go comment wraps the text in backticks, since backtick code-spans have been observed not to always survive the sync into MDX.

If a sync introduces this: wrap the offending span in backticks in the synced `.mdx` file as an immediate fix (it will be overwritten by the next sync, so also fix the source Go doc-comment to use backticks, and flag the sync pipeline if backticks were already present in the source but stripped in transit).

### Tyk Operator CRD Reference

The Tyk Operator CRD reference page at `product-stack/tyk-operator/crd-reference.mdx` imports its field content from `/snippets/operator-crd-reference.mdx`, which is auto-generated from the Tyk Operator CRD schemas and must not be edited directly. To change a field description, edit the Go doc-comments in the `tyk-operator-internal` repository.

---

## Context

This repository contains technical documentation for Tyk products. The primary audience is developers integrating with or operating Tyk. Documentation is increasingly consumed by AI agents as well as humans, so accuracy and consistency of terminology are essential. Ambiguous or inconsistent language creates errors downstream.

---

## Writing Style Rules

Apply these rules to all content in this repository.

### Product Names

- Tyk product names are always capitalised: Tyk Gateway, Tyk Dashboard, Tyk Pump, Tyk Operator, Tyk Portal, Tyk MDCB.
- Use the full product name (for example, Tyk Dashboard) rather than the short form (Dashboard) to avoid confusion with generic terms.
- When a word is used generically and does not refer to the Tyk component, do not capitalise it. For example: "a gateway" (generic), "Tyk Gateway" (the product).
- Avoid repeating the full product name in close proximity. Once established as the subject, use "it", "its", or a descriptive shorthand (such as "registered APIs" instead of "APIs registered on Tyk Gateway") to avoid awkward repetition.

### Language

- No em-dashes (—) or en-dashes (–). Use a hyphen or restructure the sentence instead. Em-dashes and en-dashes are associated with AI-generated content and should be avoided.
- Do not use "like" to mean "such as" or "for example". Use those words explicitly.
- Use "such as" or "for example" when introducing examples.
- Use American English spelling for general terminology: "behavior" not "behaviour", "authorization" not "authorisation", "color" not "colour", and so on.
- Exception: Tyk-specific proper nouns that use British spelling must retain that spelling and be capitalised to signal they are intentional. Examples: Organisation, Synchroniser. Do not correct these to American English.

### Lists

- End each bullet with a full stop if the bullet is a complete sentence.
- Do not add a full stop if the bullet is a fragment, a label, or a value (such as a field name, filename, or short noun phrase).

### Headings

- All headings use Title Case (capitalise all major words).
- This applies to `##`, `###`, and any bold text used as a heading substitute.

### API Definition Types

- Always use the full names "Tyk OAS APIs" and "Tyk Classic APIs". Never shorten to "OAS APIs" or "Classic APIs" alone. "OAS" in isolation could be confused with the OpenAPI Specification standard, which is a distinct concept.
- When content covers both Tyk OAS and Tyk Classic API definitions, always present Tyk OAS first.
- Tyk Classic is the legacy approach. Do not state this explicitly, but structure content to guide users towards Tyk OAS.
- Write as if Tyk OAS is the default. Introduce Tyk Classic behaviour with "If using Tyk Classic, ..." rather than labelling both options symmetrically.

### Structure

- Progressive disclosure: introduce the concept before Tyk-specific terminology or configuration detail.
- Link to dedicated pages for detail rather than expanding inline.
- Aim for short pages. If a page is growing large, consider whether a concept deserves its own page.

### Diagrams

- When suggesting diagrams, include a comment block with instructions for the designer covering: purpose, structure, key visual elements, and design notes.
- Use `{/* ... */}` comment syntax in MDX files for diagram placeholders.

---

## STE100 Style Check

This repo has tooling to check content against ASD-STE100 Simplified Technical English (short sentences, active voice, imperative procedure steps). It targets the same failure modes AI-generated prose tends to produce.

- `ste.yaml` (repo root) is the project config. It disables the dictionary-based rules (`approved-words`, `approved-form`, `abbreviation`, `punctuation`, `numbers`) because ASD-STE100's ~1,000-word aviation-maintenance dictionary doesn't cover general API vocabulary or Tyk product names. Only the style rules run: `sentence-length`, `passive-voice`, `ing-form`, `procedure-step`, `modal-verb`, `one-instruction`, `paragraph-length`, `noun-cluster`.
- `scripts/ste_check.py` is the wrapper. It diffs a branch against a base ref (default `origin/main`), strips YAML frontmatter/imports/JSX lines before checking (those aren't prose), and shells out to the `ste` CLI. Install the CLI with `go install github.com/probelabs/ste/cmd/ste@latest`.
  - `python3 scripts/ste_check.py` — check the current branch's diff before opening a PR.
  - `python3 scripts/ste_check.py path/to/file.mdx` — check a specific file directly, no git diff involved.
- `.github/workflows/ste100-check.yml` runs this as an advisory (non-blocking) PR comment on any PR touching `.mdx`/`.md` files. It does not gate merging. Not present on `production` (separate workflow/scripts set, no auto-sync from `main`).

Known false positives and rule limitations. Don't try to fix these by rewording; they're accepted residuals:
- `procedure-step` flags ordinary software verbs (`Configure`, `Restart`, `Create`, `Login`, `Import`, `Bind`, `Serve`, and similar) as "not an approved imperative verb". This is ASD-STE100's closed aviation-maintenance verb list; there's no config escape hatch (confirmed: adding a verb to `technical_names` does not suppress it). Only treat a `procedure-step` finding as real when the step doesn't open with a verb at all (for example it starts with "The", "This", "You", "If", "It").
- `ing-form` sometimes flags nouns that merely end in "-ing" as if they were gerunds, for example "string" (as in "connection string"), "signing" (as in "signing key"), "Operating" (as in "Operating System"). These are real compound technical terms, not verb forms, leave them as is.
- Short list items that read as fragments or labels (matching the Lists rule above, such as `- Your **Organization Name**`) can still trip `sentence-length`/`procedure-step` because the parser merges adjacent short lines into one pseudo-sentence. Treat these as accepted residuals rather than rewriting the list.
