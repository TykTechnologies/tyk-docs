# 4. Navigation

## 4.1 Top-level Tabs

**The axis is: what is the reader operating on?** Their APIs (the data plane), the Tyk deployment (install and day-2 operations), or the Tyk control plane (the Dashboard). Journey ordering applies *within* a tab, not across tabs.

| Tab | Operating on | Contents |
| :---- | :---- | :---- |
| **Home** | Docs intro | Docs home page |
| **Overview** | Orientation | Platform overview, Tyk components, deployment options (`apim`), plan your API integration, release policy, community and support (including FAQ), docs contribution |
| **Deploy & Operate** | The Tyk deployment | Install (Self-Managed, Open Source, air-gapped), Helm charts, architecture and scaling (MDCB, API sharding, Pump), configure for production, automate (Operator, Sync), upgrade and troubleshoot, release notes, plus its Reference group (component configuration and Tyk API references) |
| **API Management** | Your APIs (data plane) | Getting started, design & create, secure, control traffic, route, transform, observe, maintain, guides |
| **Platform Management** | The Tyk control plane (Dashboard) | Dashboard overview, govern APIs, Dashboard analytics, user management, TIB/SSO, guides |
| **API Publishing** | Your API consumers | Developer Portal: installation, API products and plans, consuming APIs, user management, portal administration, troubleshooting, legacy Classic Portal, plus its Reference group |
| **AI Management** | AI and MCP traffic | MCP Gateway, AI Studio |
| **Cloud** | Tyk Cloud | Getting started, management, configuration, developer support |

## 4.2 The New-tab Test

The eight tabs above are the baseline. Before you propose a new top-level tab, check that it meets **all five** conditions:

1. A distinct primary persona who does not otherwise use the platform  
2. Its own object model and vocabulary that does not map to existing tab nouns  
3. Its own installation and authentication surface  
4. 15 or more pages  
5. Fewer than 20% of its pages needing to link out to core platform content

## 4.3 Where Type Appears in Navigation

Doc Type lives in frontmatter. Two exceptions, because these types are what readers look for by name:

- **Reference** — permitted as a group label, once per tab  
- **Troubleshooting** — permitted as a group label

Everything else is labelled by task domain, not genre.

## 4.4 Structural Limits

| Rule | Target |
| :---- | :---- |
| Group nesting below a tab | Max 3 levels |
| Children per group | Min 2, target 3–7 |
| Tabs | Max 8 |
| Sibling types within a group | Homogeneous — do not mix deployment models with components |


Previous: [3. Content Types](03-content-types.md) · Next: [5. Placement Decision Procedure](05-placement-procedure.md)
