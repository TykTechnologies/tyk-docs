# 3. Content Types

Tyk uses the four Diátaxis types plus five extensions. Every page declares exactly one in `type:` frontmatter (see [7. Frontmatter Schema](07-frontmatter-schema.md)).

## 3.1 Core Four

| Type | Serves | Reader is | Must not contain |
| :---- | :---- | :---- | :---- |
| `concept` | Understanding | Studying, not yet working | Numbered procedures; exhaustive parameter tables |
| `tutorial` | Learning by doing | On rails, following our example | Choices, alternatives, "depending on your setup" |
| `how-to` | Achieving a goal | Working on their own problem | Teaching detours; conceptual background beyond one framing sentence |
| `reference` | Looking something up | Mid-task, needs a fact | Procedures; narrative explanation; opinions |

**Classification rule** — Apply the Diátaxis compass:

| If the content… | …and serves the user's… | …then it is… |
| :---- | :---- | :---- |
| informs action | acquisition of skill | `tutorial` |
| informs action | application of skill | `how-to` |
| informs cognition | application of skill | `reference` |
| informs cognition | acquisition of skill | `explanation` → our `concept` |

Two questions: *action or cognition? acquisition or application?*

If a draft resists classification, it is almost always two pages. Split it.

## 3.2 Extensions

| Type | Definition | Notes |
| :---- | :---- | :---- |
| `landing` | Section front door: what this area covers, who it is for, where to go next | Not a smuggled concept page. See §3.3. |
| `troubleshooting` | Symptom → cause → resolution | See §3.4. |
| `release-notes` | What changed in a release | Generated or semi-generated where possible |
| `glossary` | Terms and definitions | One per docset, not per product |
| `migration` | Moving from X to Y, one-way, time-bounded | Has an expiry review date |

No other values are permitted. Adding a type requires an IA decision record (see the placement procedure's escalation step in [5. Placement Decision Procedure](05-placement-procedure.md)).

## 3.3 The Landing Page Rule

In Mintlify, the first page in a group is that group's landing page. Pages such as `api-management/observability` and `api-management/rate-limit` have historically served as both explanation and front door, which are different jobs.

**Rule** — Every group with three or more children has a `type: landing` first page containing, in order:

1. One or two sentences: what this area is and the problem it solves
2. Who this area is for
3. A short list of the most common tasks, linked
4. Links to the deeper concept and reference pages

A landing page is under 300 words. If it grows past that, the surplus is a `concept` page and the landing page links to it.

## 3.4 The Troubleshooting Rule

Adopted from GitLab, which has the most battle-tested public version of this:

- Troubleshooting topics are the **last** topics on a page
- A page with **five or more** troubleshooting topics splits them into a dedicated `type: troubleshooting` page
- Troubleshooting reference entries use a fixed shape: *symptom or error message* → *why this happens* → *workaround* (temporary) or *resolution* (permanent)
- Error-message titles include at least a partial message, under 70 characters

**FAQ pages are being retired.** Existing FAQ content is reclassified as `troubleshooting`, `concept`, or `reference` on next touch. No new FAQ pages. `frequently-asked-questions/*` is a frozen namespace (see [6.2 Frozen Namespaces](06-paths-and-naming.md#62-frozen-namespaces)).

## 3.5 The Layer Model

The four types are not only categories, but they are also load-bearing layers. Reference is the foundation; everything above inherits its accuracy and its errors.

Two axes, deliberately inverted:

- **Build order (what depends on what):** Reference → Concept → How-to
- **Read order (where readers arrive):** How-to / Tutorial → Concept → Reference

| Layer | Type | Grounded in | Owns | Review interval |
| :---- | :---- | :---- | :---- | :---- |
| **L0** | `reference` | The product itself — config structs, OAS specs, CRD schemas | Every parameter name, default, type, constraint, endpoint, error code | 90 days, or on spec change |
| **L1** | `concept` | L0 | Why the thing exists, how the pieces relate, trade-offs and limits | 180 days |
| **L2** | `how-to` | L1 and L0 | A goal-directed path through the machinery | 90 days |
| **—** | `tutorial` | L0 only | A guaranteed first success | 90 days |

**Tutorials sit beside the stack, not on top of it.** A tutorial must be followable with no prior reading. It depends on reference for accuracy, but it must never *require* the reader to have absorbed a concept first — the moment it does, it has become a how-to. This is the one place where our layer model and orthodox Diátaxis could be read as disagreeing, and Diátaxis is right: tutorials deliberately withhold explanation.

### Rules

**L1 — Canonical facts live at the lowest layer that can own them.** A parameter name, default value, type, or limit is stated once, in reference. A how-to that hardcodes `default: 60s` is a defect, not a convenience: it will silently go stale on the next minor release. Higher layers name the setting and link to it.

**L2 — Link down freely, link up sparingly.** Concepts and how-tos link into reference wherever a fact is needed. Reference links upward only from a `Related` block at the end — never mid-table. A reference page's job is to be scanned, not to send the reader elsewhere.

**L3 — No orphan layers.** Reference with no concept above it is undiscoverable. A concept with no reference below it is unfalsifiable. A how-to with no concept behind it teaches cargo-cult configuration. Each is a gap worth an issue.

**L4 — Change propagates upward.** A change to an L0 page flags every page that links to it for review in the same PR. A change to an L2 page propagates nowhere. This makes blast radius visible and is the strongest argument for keeping facts at L0.

**L5 — Generate L0 wherever the source allows.** Hand-written reference is a liability with a half-life. Tyk already generates the API reference from OpenAPI in `docs.json`; the same should apply to Gateway and Dashboard configuration, Pump and MDCB environment variables, and Operator CRDs. Anything hand-maintained at L0 needs a named owner (Andy) and the shortest review interval.

Previous: [2. Principles](02-principles.md) · Next: [4. Navigation](04-navigation.md)
