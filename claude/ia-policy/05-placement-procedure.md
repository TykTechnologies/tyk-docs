# 5. The Placement Decision Procedure

Run this in order. Stop at the first step that resolves.

**Step 1 — Is this product documentation?** No → *Support & releases* (contributing, release policy, support) and stop. Yes → continue.

**Step 2 — Classify the type.** Apply the compass in [3.1 Core Four](03-content-types.md#31-core-four). Record the answer; it becomes `type:` frontmatter. If the draft contains two types, split it into two pages now. Do not proceed with a mixed page.

**Step 3 — Identify the tab, then the group.** First ask *what is the reader operating on?* — their APIs, Tyk itself, their API consumers, AI traffic, or getting unstuck. Then, within the tab, place by journey stage.

Tie-breakers, in order:

1. Configuring a Tyk component is *Platform Operations*. Configuring behaviour that an API exhibits is *API Management* — even when the setting lives in the Dashboard.
2. If two groups within a tab fit, choose the **earlier** stage in the lifecycle and cross-link from the later one.
3. If the content is meaningful only to someone already deep in another group, it belongs to that group.
4. If it is a concept applying across products, it stays in one place with badges (see [4.5 Products as Badges, Not Places](04-navigation.md#45-products-as-badges-not-places)). It is never duplicated per product.
5. If unresolved, raise in `#docs` for a review decision and record it.

**Step 4 — New page, or a section on an existing page?**

Create a **new page** if any is true:

- The content is a different `type` from the host page
- The host page would exceed roughly 1,500 words or seven H2s
- The content needs its own URL for support, search, or release-note linking
- It has different product or version applicability than the host page

Otherwise, add a section to the existing page.

**Step 5 — New group, or an existing group?**

Create a **new group** only if all are true:

- Three or more pages will share it at creation time (not "eventually")
- A reader would look for those pages together
- Depth stays within [4.4 Structural Limits](04-navigation.md#44-structural-limits)
- The label is a task domain, not a genre (see [4.3 Where Type Appears in Navigation](04-navigation.md#43-where-type-appears-in-navigation))

Otherwise, place in the nearest existing group.

**Step 6 — Choose the path and filename.** See [6. Paths and Naming](06-paths-and-naming.md).

**Step 7 — Write frontmatter.** See [7. Frontmatter Schema](07-frontmatter-schema.md).

**Step 8 — Wire it up.** Add to `docs.json`. Add inbound links from the relevant landing page and at least one sibling. Add redirects if anything moved (see [6.4 Redirects](06-paths-and-naming.md#64-redirects)).

Previous: [4. Navigation](04-navigation.md) · Next: [6. Paths and Naming](06-paths-and-naming.md)
