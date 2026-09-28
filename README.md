!["Tyk Docs"](/img/logos/tyk-docs-logo-dark.svg)

# Tyk Documentation

This repository is the source of the official [Tyk documentation](https://tyk.io/docs/). The docs cover Tyk Gateway (open source), Tyk Dashboard, the Developer Portal, MCP Gateway, Tyk AI Studio and Tyk Cloud. The site is built with [Mintlify](https://mintlify.com/).

## Read the Docs

- [Tyk documentation](https://tyk.io/docs/)
- [Tyk Open Source Gateway quick start](https://tyk.io/docs/deployment-and-operations/tyk-open-source-api-gateway/quick-start)
- [Tyk Self-Managed quick start](https://tyk.io/docs/getting-started/quick-start)
- [Tyk Cloud: create an account](https://tyk.io/docs/getting-started/create-account)
- [Release notes](https://tyk.io/docs/developer-support/release-notes/overview)

### For AI Assistants and Agents

- [`llms.txt`](https://tyk.io/docs/llms.txt) lists the docs pages. [`llms-full.txt`](https://tyk.io/docs/llms-full.txt) contains the full text.
- Every page is also available as Markdown. Add `.md` to the page URL.
- The docs MCP server is at `https://tyk.io/docs/mcp`. Use it to search the docs from an MCP client.

## Versions

The `main` branch is the next release. It deploys to the [Nightly](https://tyk.io/docs/nightly/) docs. Each `release-5.x` branch holds the docs for that release. Versions 5.8 and later come from this repository. Versions 5.7 and earlier come from the archived [tyk-docs-hugo](https://github.com/TykTechnologies/tyk-docs-hugo) repository.

## Run the Docs Locally

You need [Node.js](https://nodejs.org/) and Git.

1. Install the Mintlify CLI:
   ```bash
   npm i -g mint
   ```
2. Clone the repository. If you are an external contributor, clone your fork.
   ```bash
   git clone https://github.com/TykTechnologies/tyk-docs.git
   cd tyk-docs
   ```
3. Start the preview server:
   ```bash
   mint dev
   ```
4. Open `http://localhost:3000` in your browser.

## Check Your Changes

Run the same validation as CI before you open a pull request. You need Python 3.

```bash
pip install requests pyyaml
python3 scripts/validate_mintlify_docs.py . --validate-redirects --verbose
```

The script finds broken internal links, missing images and redirect problems.

To check your prose against [ASD-STE100 Simplified Technical English](https://www.asd-ste100.org/), install the [`ste`](https://github.com/probelabs/ste) CLI and run the check script:

```bash
go install github.com/probelabs/ste/cmd/ste@latest
python3 scripts/ste_check.py
```

## Contribute

We welcome contributions.

1. Create a branch from `main`.
2. Edit or add `.mdx` pages. If you add a page, add it to the navigation in `docs.json`.
3. Open a pull request against `main`.

Tyk maintainers review your pull request. If necessary, they copy the change to the release branches.

Other Tyk repositories generate some files in this repository from their source code. Examples are the files in `swagger/` and the configuration snippets in `snippets/`. Do not edit these files here. [`CLAUDE.md`](CLAUDE.md) lists them and gives the style rules.

For the full workflow, see the [contribution guide](https://tyk.io/docs/developer-support/contribution-guides).

## Report a Problem

- Docs error: [open an issue](https://github.com/TykTechnologies/tyk-docs/issues/new) in this repository.
- Product question: ask on the [Tyk Community Forum](https://community.tyk.io/).
- Commercial support: see [Tyk support](https://tyk.io/docs/developer-support/support).
