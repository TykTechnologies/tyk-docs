# 4. Navigation

## 4.1 Top-level Tabs

**The axis is: what is the reader operating on?** Their APIs, or Tyk itself. Journey ordering applies *within* a tab, not across tabs.

| Tab | Operating on | Contents |
| :---- | :---- | :---- |
| **Home** | Docs Intro |  |
| **Overview** | Orientation | Site landing, platform overview, components, `apim`, plan your integration, policy |
| **API Management** | Your APIs | Design & create, secure, control traffic, route, transform, observe, maintain, plus its Reference group |
| **Platform Management** | Tyk itself | Deploy & install (OSS, Self Managed, Helm), production configuration, MDCB, Pump, Dashboard administration, users, RBAC, TIB/SSO, Governance, plus its Reference group |
| **API Publishing** | Your API consumers | Developer Portal: products, plans, catalogues, consumer management, portal administration |
| **AI Management** | AI and MCP traffic | MCP Gateway, AI Studio |
| **Cloud** | Cloud | Cloud |

## 4.2 The New-tab Test

The seven tabs above are the baseline. Before you propose a new top-level tab, check that it meets **all five** conditions:

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
| Tabs | Max 7 |
| Sibling types within a group | Homogeneous — do not mix deployment models with components |


Previous: [3. Content Types](03-content-types.md) · Next: [5. Placement Decision Procedure](05-placement-procedure.md)
