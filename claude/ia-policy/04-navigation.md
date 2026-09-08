# 4. Navigation

## 4.1 Top-level Tabs

**The axis is: what is the reader operating on?** Their APIs, or Tyk itself. Journey ordering applies *within* a tab, not across tabs.

| Tab | Operating on | Contents |
| :---- | :---- | :---- |
| **Home** | Docs Intro | |
| **Overview** | Orientation | Site landing, platform overview, components, `apim`, plan your integration, policy |
| **API Management** | Your APIs | Design & create, secure, control traffic, route, transform, observe, maintain, plus its Reference group |
| **Platform Operations** | Tyk itself | Deploy & install (OSS, Self Managed, Cloud console, Helm), production configuration, MDCB, Pump, Dashboard administration, users, RBAC, TIB/SSO, Governance, plus its Reference group |
| **API Publishing** | Your API consumers | Developer Portal: products, plans, catalogues, consumer management, portal administration |
| **AI Management** | AI and MCP traffic | MCP Gateway, AI Studio |
| **Cloud** | Cloud | Cloud |

**Tyk Cloud.** The Cloud console is a Tyk-management surface, so it belongs in *Platform Operations*: a `Tyk Cloud` group under Deploy alongside OSS and Self Managed, with console-specific administration (environments, organisations, teams) under the platform administration groups. Cloud-specific behaviour in API-level features stays in *API Management* with a `cloud` tier badge.

**Two boundary calls worth confirming**

- *Dashboard Analytics.* Split it: pump configuration and analytics storage are Tyk infrastructure → *Platform Operations*; reading and interpreting analytics is about your APIs → *API Management → Observe*.
- *Audit logs.* Under this axis the three current pages are not simply a duplication error. Gateway traffic auditing is about your APIs; Dashboard auditing is about who changed Tyk; Portal auditing is about consumer activity. They are three legitimate `how-to` pages in three tabs. What is missing is a single `concept` page explaining Tyk's audit-logging model across components — put that in *Platform Operations* and link to it from all three.

## 4.2 The New-tab Test

The six tabs above are the baseline. A new top-level tab requires **all five**:

1. A distinct primary persona who does not otherwise use the platform
2. Its own object model and vocabulary that does not map to existing tab nouns
3. Its own installation and authentication surface
4. 15 or more pages
5. Fewer than 20% of its pages needing to link out to core platform content

## 4.3 Where Type Appears in Navigation

Type lives in frontmatter. Two exceptions, because these types are what readers look for by name:

- **Reference** — permitted as a group label, once per tab
- **Troubleshooting** — permitted as a group label

Everything else is labelled by task domain, not genre. This is a CI-checked rule.

**Retired group labels (CI-checked):** `Guides`, `How-To Guides`, `Use Cases`, `Misc`, `Other`, `Advanced`.

`Guides` currently appears as a group in at least eight places and functions as the bucket for content whose type was never decided. Replace each occurrence with either a task-domain label (`Tracing backends`, `Credential management`) or, where every child is genuinely `type: how-to`, fold the children up into the parent group.

## 4.4 Structural Limits

| Rule | Limit |
| :---- | :---- |
| Group nesting below a tab | Max 3 levels |
| Children per group | Min 2, target 3-7 |
| Tabs | Max 7 |
| Sibling types within a group | Homogeneous — do not mix deployment models with components |

## 4.5 Products as Badges, Not Places

Every page declares `products:` in frontmatter (see [7. Frontmatter Schema](07-frontmatter-schema.md)). This drives:

- A visible badge on the page
- Mintlify `tag` for tier labelling (`OSS`, `Enterprise`, `Cloud`)
- Faceted filtering where supported

**Cross-product rule (needs review on first application)** — A *concept* that applies to more than one product gets **one** page, badged with all applicable products. Product-specific *procedures* may legitimately live in different tabs when the reader's object differs (§4.1, audit logs). The test is: would a reader looking for this need to know which product implements it? If no, one page. If yes, one concept plus per-product how-tos that link back to it.

Previous: [3. Content Types](03-content-types.md) · Next: [5. Placement Decision Procedure](05-placement-procedure.md)
