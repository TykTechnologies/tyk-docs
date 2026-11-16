# Release Notes

Rules for writing and updating the release notes in `developer-support/release-notes/`.

In a Helm Charts release note, the LTS version that the chart installs must match the Gateway and Dashboard image tags in tyk-charts `components/*/values.yaml` at release time, because security patches can bump them after the draft.

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
