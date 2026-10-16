# Writing Style and Repository Conventions


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


## Writing Style Rules

Apply these rules to all content in this repository.

### Product Names

- Tyk product names are always capitalised: Tyk Gateway, Tyk Dashboard, Tyk Pump, Tyk Operator, Tyk Portal, Tyk MDCB.
- When a word is used generically and does not refer to the Tyk component, do not capitalise it. For example: "a gateway" (generic), "Tyk Gateway" (the product).
- Avoid repeating the full product name in close proximity. Once established as the subject, use "it", "its", or a descriptive shorthand (such as "registered APIs" instead of "APIs registered on Tyk Gateway") to avoid awkward repetition.

### Language

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


