# 7. Frontmatter Schema

Required on every new or substantially edited page (CI-checked).

```
---
title: "Audit logs"
description: "What Tyk records in audit logs and how retention works."
type: concept                  # enum, see 3. Content Types
sidebarTitle: "Audit logs"
---
```

`type` must be one of the values defined in [3. Content Types](03-content-types.md): `concept`, `tutorial`, `how-to`, `reference`, `landing`, `troubleshooting`, `release-notes`, `glossary`, `migration`.

Previous: [6. Paths and Naming](06-paths-and-naming.md)
