# Release Notes

Rules for writing and updating the release notes in `developer-support/release-notes/`.

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
- Do not copy the pull command from an earlier release note. Each version has a different digest. If two versions show the same digest, one of them is wrong.
- Use the same format in every component release note.
- The `Check Docker image digests in release notes` CI step (`scripts/check_docker_digests.py`) compares each digest with Docker Hub.

## Latest Releases Data

The [Latest Releases](/developer-support/release-notes/overview) page gets its data from `snippets/release-data.mdx`. When you add release notes for a new version, update the entry for that component in the same PR:

- `latest` and `latestData.name`: the new version.
- `latestData.date`: the release date from the release notes, in `DD/MM/YYYY` format.
- `latestData.docker` and `latestData.tag`: links to the new version.
- `lts`: update it only when you add a patch release for the LTS line.

Do not copy the date from the previous release. The `Check Latest Releases data` CI step (`scripts/check_release_data.py`) compares this data with the release notes.

On older release branches, such as `release-5.13`, `snippets/release-data.mdx` does not exist. The data is inline in `developer-support/release-notes/overview.mdx`.

## Backports to LTS Release Branches

Component releases (MDCB, Pump, Developer Portal, Sync, Operator, Tyk Identity Broker, Helm Charts) stay compatible with the LTS versions of Tyk Gateway and Tyk Dashboard. They also contain fixes and improvements that LTS users need. For this reason, we backport their release notes to the LTS release branches.

Some new features in these releases work only with the latest Gateway or Dashboard. The pages for these features exist only on `main`. On the LTS branch, a relative link to such a page or anchor breaks, and the backport PR fails CI.

When a backport PR fails CI because of such a link:

1. Merge the latest LTS branch into the backport branch first. Another backport can add the missing page or anchor. If the link then works, keep it relative.
2. Change each link that still fails to a full URL: `https://tyk.io/docs/<path>#<anchor>`. This sends LTS readers to the latest docs for the feature, which is correct because the feature needs the latest version.
3. Make sure that each full URL opens on the live site and that the anchor exists on `main`.
4. Do not remove the feature text or the link.

The backport bot (`/release` comment) copies the original PR only. It does not include later fixes to the same release notes. Backport those fixes separately.

Run all the steps in `.github/workflows/validate-docs.yml` locally before you push. CI stops at the first failed step, so it does not show all errors at once.
