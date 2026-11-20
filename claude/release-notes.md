# Release Notes

Rules for writing and updating the release notes in `developer-support/release-notes/`.

In a Helm Charts release note, the LTS version that the chart installs must match the Gateway and Dashboard image tags in tyk-charts `components/*/values.yaml` at release time, because security patches can bump them after the draft.

## Release Notes vs Topic Pages

A release note tells the user what changed. The topic page tells the user how to use it.

- For each change, write what changed, why it matters to the user, and the config field and default. Then link to the topic page.
- Do not put step-by-step procedures, long configuration examples or concept explanations in a release note. Put them in the topic page.
- A short before/after example is permitted for a breaking change.
- If no topic page exists for the feature, write one. Do not use the release note as a substitute.
- Keep each entry to a short outline of the change. Do not add configuration tables, JSON examples, lists of endpoints or error codes, UI walkthroughs, "limitations" sub-sections or bold sub-headings inside an entry.
- Link each feature, configuration option and concept that you name to its page.

## Scope and Consistency

- Put each change only in the release note of the component that ships it. Do not add a change to another component's note because that component has a small supporting change, or because the ticket lists it.
- Include only facts that apply to the component. For example, Go plugins are a Tyk Gateway concern, so do not mention them in a Tyk Dashboard release note. The Developer Portal integrates with Tyk Dashboard, so do not mention it in a Tyk Gateway release note.
- For a feature that spans components, describe each component's own part in its note, for example the API Designer UI in Tyk Dashboard and the configuration field in Tyk Gateway.
- Do not name the component in its own release note, in titles or in body text. Write "This release adds ...", not "Tyk Pump 1.15.0 adds ...".
- When the same change ships in several components, use the same wording in each note. Change only the component name and the configuration path.
- When the same fix ships in an LTS patch and in a new minor release, use the same wording in both notes.
- Use only the sections that the component's existing release notes use. For example, do not add a Dependencies section to a Developer Portal release note.
- Make Highlights, Breaking Changes, Deprecations and the changelog agree. Each feature or deprecation in Highlights must have a changelog entry. If the changelog deprecates an option, add it to Deprecations.
- Do not recommend a specific older version. Do not promise a future fix. The standing guidance is to use the latest version.
- Do not publish details of a security weakness that someone could exploit.

## Release Highlights

- Do not open Highlights with a summary paragraph when the section has highlight entries.
- Highlights are the most important changes, not a summary of the changelog. Put the most important feature first.
- Give each highlighted feature a bold heading that names the user-facing capability, one or two sentences, and a link to the feature page.
- Do not list routine items in Highlights, such as Go version updates, CVE fixes, dependency updates or minor fixes. Put them in the changelog.
- For a patch release, write a short summary and call out only items the user must act on. Do not list each fix.
- For a release that only fixes CVEs, write: "This is a security patch release. It contains no functional or behavioral changes; it addresses several CVEs identified in dependent libraries."
- In a Helm Charts release note, state the component versions that the chart installs by default.

## Breaking Changes and Deprecations

- Put a change in Breaking Changes if it changes default behavior or can break an existing deployment. Do not mention it only in the changelog. A new `allow_unsafe_*` opt-out option is a sign of a breaking change.
- For each breaking change, give the previous behavior, what changed, who is affected, what happens to them and what to do. Give any opt-out option with its full path and default. If the opt-out weakens security, recommend it only as a temporary measure.
- Do not write "There are no breaking changes" when a change can affect existing users. For example, a Go version update in Tyk Gateway means users must rebuild their custom Go plugins. State the condition and link to the details.
- In the changelog entry for a breaking change, write "This may affect existing <items>. See [Breaking Changes](#breaking-changes) for details."
- For a deprecation, give the full configuration path with a link, the version that deprecated it, the reason and the replacement.

## Changelog Entries

- Write accordion titles as a short phrase that names the user-visible capability or problem. Start with a past-tense verb, such as "Added" or "Fixed". Do not add tags such as "[UI]" or internal names.
  - Do: "Fixed Incorrect X-RateLimit-Reset Timestamp"
  - Don't: "Fix route priority logic for ValidateRequest middleware"
- Use "Resolved CVEs" as the title of the security fixes accordion.
- Put a bug fix under Fixed, even when the work is large. Put a new option or an enhancement under Added, even when it solves a reported problem.
- Do not add a Fixed entry for a bug in a feature that is new in the same release, because users never had the bug.
- In a Fixed entry, start with the symptom that the user saw and the condition, for example "Fixed an issue where <symptom> could occur when <condition>." Then, in a new paragraph, describe the corrected behavior. Do not describe the code change.
- If the fix resolves a regression, state the version that introduced it.
- Do not use "now" for a new feature, because there was no previous behavior. Use "now" only when existing behavior changes.
- When an Added entry extends an existing feature, first state the existing behavior. Then describe the change and its effect.
- State backward compatibility in concrete terms, for example "There is no change in behavior for existing Sessions."
- Merge related changes into one entry. Remove an entry that another entry already implies. Keep all the ticket IDs in the comment of the merged entry.
- Order entries by importance. Put major features first.
- Write full sentences in entry bodies, for example "We have added ...". Do not write a single bullet fragment.

## Downloads

- In a release note for a version that is not LTS, add this note: `<Note>Tyk Helm Charts are configured to install the LTS version of Tyk <Component>. You will need to modify them to install v<version>.</Note>`

## Docker Image Digests

Each release note lists the Docker images for the release in the **Downloads** section. The pull command for each image must use the tag and the SHA256 digest. Do not add a pull command that uses only the tag. A digest identifies an immutable image. A tag can move.

````markdown
- [Docker Image to pull](https://hub.docker.com/r/tykio/tyk-dashboard/tags?page=&page_size=&ordering=&name=v5.16.0)
  - ```bash
    docker pull tykio/tyk-dashboard:v5.16.0@sha256:b358479ee285a29a981c9256482a11b3958c170659960d614782f4a7b85e6933
    ```
````

- Use the digest of the multi-architecture image index. Do not use the digest of a single-platform manifest. Get it with:

  ```bash
  docker buildx imagetools inspect tykio/<image>:<tag> | awk '/^Digest:/ {print $2}'
  ```

- Get the digest from the published image after the release. Do not copy it from a ticket, a draft or a CI log.
- Use the same format in every component release note.


## Backports to LTS Release Branches

Component releases (MDCB, Pump, Developer Portal, Sync, Operator, Tyk Identity Broker, Helm Charts) stay compatible with the LTS versions of Tyk Gateway and Tyk Dashboard. They also contain fixes and improvements that LTS users need. For this reason, we backport their release notes to the LTS release branches.

Some new features in these releases work only with the latest Gateway or Dashboard. The pages for these features exist only on `main`. On the LTS branch, a relative link to such a page or anchor breaks, and the backport PR fails CI.

When a backport PR fails CI because of such a link:

1. Merge the latest LTS branch into the backport branch first. Another backport can add the missing page or anchor. If the link then works, keep it relative.
2. Change each link that still fails to a full URL: `https://tyk.io/docs/<path>#<anchor>`. This sends LTS readers to the latest docs for the feature, which is correct because the feature needs the latest version.
