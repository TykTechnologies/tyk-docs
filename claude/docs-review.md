# Reviewing Documentation PRs

Rules for reviewing a documentation PR and for applying review suggestions. They come from recurring review feedback on new and updated pages. Use them together with the [writing style rules](writing-style-and-conventions.md) and the [IA policy](ia-policy/01-purpose-and-scope.md).

## Review Order

Review the content first. Crisp wording, duplicate facts, and long paragraphs are the main findings. TODOs, availability wording, and code checks come second. A review that lists only TODOs misses the content problems.

Structure a review body in this order:

1. **Content**: duplicate facts, long paragraphs, unclear wording, and contradictions. Show duplicate facts in a table with the fact, where it appears, and where to keep it.
2. **Placement**: navigation and the base branch.
3. **TODOs**: screenshots, reference links, and diagram comments.
4. **Code checks**: the facts that you verified, with file paths. Also list the facts that you did not verify.
5. **Open questions**: the answers to the open questions in the PR description, and the questions that remain.

## Duplication

- Count how often one fact appears on the page and on its neighbour pages. Keep one definition. Change the others to a link.
- Remove prose that repeats a table on the same page.
- If a paragraph repeats a list, keep only the new fact from the paragraph.
- Do not repeat the upgrade steps of a release on a topic page. If the release notes have them, link to the release notes.
- If a configuration field is in the environment variable or configuration reference, link to the reference. Do not repeat its default and format in a table on the page.

## Length and Shape

- On a short how-to, the overview is one or two sentences. A long page can keep a longer overview.
- Split a paragraph or a table cell that has more than three or four sentences. Use a list, or shorter sentences.
- A table with one wide prose column next to short columns reads badly. Change it to a numbered list with a description for each item.
- If one list item contains many settings, put the settings in sub-bullets.
- One page, one job. A section can apply to more than the subject of the page. Move such a section to its own page. Link to it from each page that needs it.

## Wording

- Do not start a page with a "This page describes:" list.
- Do not use filler lead-ins, such as "You need:", "Keep these points in mind:", or "as follows".
- Give one option for each task. On a how-to, remove "You can also use A, B, or C" alternatives.
- Remove statements that are obvious to the reader, and trailing clauses that give no action.
- Move an edge-case caveat into the item that it qualifies.
- Do not put parenthetical qualifiers in titles.
- Use "region", not "site", for deployments in more than one location.

## Availability

- On a page with an **Availability** section, write one sentence after the table. For example: "Agent tracing is available from Tyk AI Studio 2.3.0." The table gives the edition.
- Put an edition caveat on the field or step that it qualifies, not in the **Availability** section.
- Check that each edition link goes to the anchor of that edition.

## Sections to Leave Out

- Do not end a how-to with a **Limitations**, **Known Issues**, or **Related Pages** section. Move each item into the section that it qualifies. Delete an item that repeats the page.
- Do not add a **Troubleshooting** section to a concept or architecture page.

## Version Accuracy

- Do not document a feature that no release includes. An example is code that is only on the main branch of another repository. Check the release tags, the PR labels, and the fix version of the Jira ticket. Replace the content with a TODO that names the ticket.
- A later release can change a default or lift a limit. Then scope the old statement, for example "In v2.2, ...". Do not delete it. Look for the same statement on neighbour pages.
- When the code, the documentation in the product repository, internal documents, and changelogs disagree, the code decides.
- Verify Helm value keys against `values.yaml` and the templates of the chart.

## TODO Comments

Use these formats:

| Purpose | Format |
| :--- | :--- |
| A UI step with no screenshot | `{/* TODO: Add screenshot: <what the screenshot shows> */}` |
| A configuration field with no reference link | `{/* TODO: link reference for <NAME> */}` |
| A table of environment variables with no reference links | `{/* TODO: Add reference links to each environment variable. */}` |
| A link to a page that is not merged yet | `{/* TODO: link to <page> once merged */}` |

- Add a screenshot TODO at each UI step, such as a form, a panel, or a dialog.
- Put a screenshot TODO after a numbered list, not between its items. A comment between items breaks the list for the STE check.
- When you add a page, search for TODOs that wait for it. Replace them with links in the same PR.
- For diagrams, use the designer comment block from the [writing style rules](writing-style-and-conventions.md#diagrams).

## Placement

- A how-to that configures an existing installation goes in **Installation > Configuration**. Link it from the related architecture or deployment page.
- A page about usage, metrics, or analytics goes with the monitoring pages, not with the feature that it measures.
- A PR for a release targets the integration branch of that release, not `main`. A fix to a neighbouring page goes in its own PR.

## Applying Review Suggestions

- Fetch the PR branch before you edit. A resolved thread does not mean that the change is in the file. Compare the file with the suggestion.
- Apply the suggestions of each file from the bottom of the file to the top. Then the line numbers stay correct. Check that no two suggestions change the same lines.
- After you apply the suggestions, check for new double blank lines and for code fences that do not close.
- Run the steps of `validate-docs.yml` and the STE check. Compare the STE error count with the count before the change, and fix each new error.
- To update a PR branch, merge the base branch into it. Do not rebase or force-push.
- Reply on each thread with the commit SHA, then resolve the thread.
- Update the PR description when a change answers an open question.

## Bot Review Comments

- Act on wording contradictions and factual conflicts, after you check them against the code.
- Do not add warnings that a bot suggests for edge risks, or changes that criticize the product design.
