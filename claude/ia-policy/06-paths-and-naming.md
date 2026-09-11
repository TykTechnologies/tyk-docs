# 6. Paths and Naming

Paths are **stable permalinks**. Navigation position may change freely; a published URL may not.

## 6.1 Sanctioned Namespaces

New files go in exactly one of these (CI-checked):

| Namespace | Contents |
| :---- | :---- |
| `api-management/` | Gateway and core API lifecycle features |
| `platform-management/` | Dashboard, users, RBAC, governance, categories, templates |
| `portal/` | Developer Portal (Enterprise) |
| `ai-management/` | MCP Gateway, AI Studio |
| `deployment/` | Installation, configuration, production operations |
| `developer-support/` | Release notes, release policy, contributing, deprecation |

Path shape: `<namespace>/<domain>/<slug>` — two or three segments after the namespace, never more.

## 6.2 Frozen Namespaces

No new files. Existing files stay where they are and are not moved.

`tyk-stack/` · `product-stack/` · `getting-started/` · `key-concepts/` · `basic-config-and-security/` · `advanced-configuration/` · `transform-traffic/` · `planning-for-production/` · `configure/` · `tyk-configuration-reference/` · `deployment-and-operations/` · `troubleshooting/` · `frequently-asked-questions/` · `tyk-developer-portal/` · `tyk-apis/` · `tyk-identity-broker/` · `tyk-multi-data-centre/` · `tyk-pump/` · `tyk-dashboard/` · `tyk-oss-gateway/` · `tyk-self-managed/` · `use-cases/` · `tyk-governance/`

## 6.3 Filename Patterns by Type

| Type | Pattern | Example |
| :---- | :---- | :---- |
| `landing` | `overview` | `api-management/observability/overview` |
| `concept` | `<topic>` — noun phrase | `api-management/rate-limiting` |
| `how-to` | `how-to-<verb>-<object>` | `ai-management/mcp-gateway/how-to-block-tool` |
| `tutorial` | `quickstart` or `tutorial-<outcome>` | `deployment/quickstart` |
| `reference` | `<thing>-reference` or `<thing>-configuration` | `deployment/gateway-configuration` |
| `troubleshooting` | `troubleshoot-<area>` | `portal/troubleshoot-cors` |

The MCP Gateway `how-to-*` set is the reference implementation for how-to naming.

## 6.4 Redirects

- Any file rename, move, or deletion requires a redirect entry in the same PR
- Deprecated pages keep their URL until removal, then redirect to the replacement or the nearest landing page

Previous: [5. Placement Decision Procedure](05-placement-procedure.md) · Next: [7. Frontmatter Schema](07-frontmatter-schema.md)
