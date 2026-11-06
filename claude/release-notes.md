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
- Use the same format in every component release note.
