"""Render release notes sections into tyk-docs markdown/HTML format."""

from __future__ import annotations

from release_notes_generator.config import get_product_config
from release_notes_generator.models import ChangelogEntry, ReleaseSection


def render_release_section(section: ReleaseSection, release_highlights: str = "", is_new_minor: bool = False) -> str:
    parts: list[str] = []
    if is_new_minor:
        parts.append(f"## {section.major_minor} Release Notes")
        parts.append("")
    parts.append(f"### {section.version} Release Notes")
    parts.append("")
    parts.append(f"#### Release Date {section.release_date}")
    parts.append("")
    parts.append("#### Release Highlights")
    parts.append("")
    if release_highlights:
        parts.append(release_highlights.replace("VERSION", section.version))
    else:
        parts.append(f'This release focuses mainly on bug fixes. For a comprehensive list of changes, please refer to the detailed [changelog]({{{{< ref "#Changelog-v{section.version}">}}}}) below.')
    parts.append("")
    parts.append("#### Breaking Changes")
    if section.breaking_changes:
        parts.append("")
        for e in section.breaking_changes:
            parts.append(f"- **{e.summary_line}**: {e.breaking_description or e.detail_text}")
        parts.append("")
    else:
        parts.append("There are no breaking changes in this release.")
    parts.append("")
    parts.append(f"#### Dependencies {{#dependencies-{section.version}}}")
    parts.append("")
    parts.append(_render_dependencies_placeholder(section))
    parts.append("")
    parts.append("#### Deprecations")
    parts.append("There are no deprecations in this release.")
    parts.append("")
    parts.append("")
    parts.append(f"#### Upgrade instructions {{#upgrade-{section.version}}}")
    parts.append(f"If you are upgrading to {section.version}, please follow the detailed [upgrade instructions](#upgrading-tyk).")
    parts.append("")
    parts.append("#### Downloads")
    pc = get_product_config(section.product)
    if pc.docker:
        parts.append(f"- [Docker image to pull](https://hub.docker.com/r/{pc.docker}/tags?page=&page_size=&ordering=&name=v{section.version})")
        parts.append(f"  - ```bash")
        parts.append(f"    docker pull {pc.docker}:v{section.version}")
        parts.append(f"    ``` ")
    parts.append("- Helm charts")
    parts.append('  - [tyk-charts]({{<ref "developer-support/release-notes/helm-chart" >}})')
    parts.append("")
    if pc.source_repo:
        parts.append(f"- [Source code tarball for OSS projects](https://github.com/{pc.source_repo}/releases)")
        parts.append("")
    parts.append(f"#### Changelog {{#Changelog-v{section.version}}} ")
    parts.append("")
    cats = [("Added", section.added), ("Changed", section.changed), ("Fixed", section.fixed), ("Security Fixes", section.security_fixes)]
    for name, entries in cats:
        if entries:
            parts.append(f"##### {name}")
            parts.append("")
            parts.append("<ul>")
            for e in entries:
                parts.extend(["<li>", "<details>", f"<summary>{e.summary_line}</summary>", "", e.detail_text, "</details>", "</li>"])
            parts.append("</ul>")
            parts.append("")
    if not any(entries for _, entries in cats):
        parts.append("No changes in this release.")
        parts.append("")
    return "\n".join(parts)


def _render_dependencies_placeholder(section: ReleaseSection) -> str:
    return f"""
##### Compatibility Matrix For Tyk Components
<!-- TODO: Fill in compatibility matrix for this release -->
| Gateway Version | Recommended Releases | Backwards Compatibility |
|----    |---- |---- |
| {section.version} | MDCB vX.Y.Z     | MDCB vX.Y.Z |
|         | Operator vX.Y.Z  | Operator vX.Y |
|         | Sync vX.Y.Z    | Sync vX.Y.Z |
|         | Helm Chart vX.Y  | Helm all versions |
| | EDP vX.Y | EDP all versions |
| | Pump vX.Y.Z | Pump all versions |
| | TIB (if using standalone) vX.Y.Z | TIB all versions |

##### 3rd Party Dependencies & Tools

<!-- TODO: Update third-party dependency versions -->
| Third Party Dependency                                       | Tested Versions        | Compatible Versions    | Comments |
| ------------------------------------------------------------ | ---------------------- | ---------------------- | -------- |
| [Go](https://go.dev/dl/)                                     | X.YZ  |  X.YZ  | [Go plugins]({{{{< ref "api-management/plugins/golang" >}}}}) must be built using Go X.YZ |
| [Redis](https://redis.io/download/)  | 6.2.x, 7.x  | 6.2.x, 7.x  | Used by Tyk Gateway |
| [OpenAPI Specification](https://spec.openapis.org/oas/v3.0.3)| v3.0.x                 | v3.0.x                 | Supported by [Tyk OAS]({{{{< ref "api-management/gateway-config-tyk-oas#tyk-oas-api-definition-object" >}}}}) |

Given the potential time difference between your upgrade and the release of this version, we recommend users verify the ongoing support of third-party dependencies they install, as their status may have changed since the release."""
