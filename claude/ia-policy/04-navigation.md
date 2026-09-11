## 4\. Navigation

### 4.1 Top-level tabs

**The axis is: what is the reader operating on?** Their APIs, or Tyk itself. Journey ordering applies *within* a tab, not across tabs.

| Tab | Operating on | Contents |
| :---- | :---- | :---- |
| **Home** | Docs Intro |  |
| **Overview** | Orientation | Site landing, platform overview, components, `apim`, plan your integration, policy |
| **API Management** | Your APIs | Design & create, secure, control traffic, route, transform, observe, maintain, plus its Reference group |
| **Platform Operations** | Tyk itself | Deploy & install (OSS, Self Managed, Helm), production configuration, MDCB, Pump, Dashboard administration, users, RBAC, TIB/SSO, Governance, plus its Reference group |
| **API Publishing** | Your API consumers | Developer Portal: products, plans, catalogues, consumer management, portal administration |
| **AI Management** | AI and MCP traffic | MCP Gateway, AI Studio |
| **Cloud** | Cloud | Cloud |

### 4.2 The new-tab test

The six tabs above are the baseline. A new top-level tab requires **all five**:

1. A distinct primary persona who does not otherwise use the platform  
2. Its own object model and vocabulary that does not map to existing tab nouns  
3. Its own installation and authentication surface  
4. 15 or more pages  
5. Fewer than 20% of its pages needing to link out to core platform content

### 4.3 Where type appears in navigation

Doc Type lives in frontmatter. Two exceptions, because these types are what readers look for by name:

- **Reference** — permitted as a group label, once per tab  
- **Troubleshooting** — permitted as a group label

Everything else is labelled by task domain, not genre.

### 4.4 Structural limits

| Rule | Limit |
| :---- | :---- |
| Group nesting below a tab | Max 3 levels |
| Children per group | Min 2, target 3–7 |
| Tabs | Max 7 |
| Sibling types within a group | Homogeneous — do not mix deployment models with components |

### 4.5 Products as badges, not places

Every page declares `products:` in frontmatter (§7). This drives:

- A visible badge on the page  
- Mintlify `tag` for tier labelling (`OSS`, `Enterprise`, `Cloud`)  
- Faceted filtering where supported
