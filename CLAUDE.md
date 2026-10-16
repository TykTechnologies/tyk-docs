# Rules for AI Assistant

This repository contains technical documentation for Tyk products. The primary audience is developers integrating with or operating Tyk.

The rules are split into two areas. Read both before making non-trivial changes.

## Writing Style and Repository Conventions

[`claude/writing-style-and-conventions.md`](claude/writing-style-and-conventions.md) covers:

- Auto-generated files you must not edit directly
- Writing style rules (product names, language, lists, headings, API definition types, structure, diagrams)
- The STE100 Simplified Technical English style check

## Information Architecture Policy

Given a piece of content, where does it go? [`claude/ia-policy/`](claude/ia-policy/01-purpose-and-scope.md) answers this. It governs content types, navigation placement, file paths and naming, and recommended frontmatter. It does not govern voice, grammar, or formatting; that is the writing style rules above.

1. [Purpose and Scope](claude/ia-policy/01-purpose-and-scope.md)
2. [Principles](claude/ia-policy/02-principles.md)
3. [Content Types](claude/ia-policy/03-content-types.md)
4. [Navigation](claude/ia-policy/04-navigation.md)
5. [The Placement Decision Procedure](claude/ia-policy/05-placement-procedure.md)
6. [Paths and Naming](claude/ia-policy/06-paths-and-naming.md)
7. [Frontmatter Schema](claude/ia-policy/07-frontmatter-schema.md)

Before you place or restructure content, use the procedure in file 5 as a guide.

### How to use the IA policy

The IA policy describes the target state of the docs. It is guidance, not a gate.

- Most existing pages do not follow the policy yet. This is expected.
- Apply the policy to new pages where it makes sense.
- On pages that you edit, you can suggest improvements that move them toward the policy.
- Do not block a PR, refuse a placement, or restructure unrelated pages because of the policy.
- If the policy conflicts with the conventions of nearby pages, keep the page consistent with its neighbours. Mention the difference in the PR description.
- No CI check enforces the policy.
- The policy will change as the docs improve. If a rule does not fit real content, propose a change to the policy.
