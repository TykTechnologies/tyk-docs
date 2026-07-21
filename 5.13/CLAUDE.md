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

- Always use the full names "Tyk OAS" and "Tyk Classic". Never shorten to "OAS" or "Classic" alone. "OAS" in isolation could be confused with the OpenAPI Specification standard, which is a distinct concept.
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
