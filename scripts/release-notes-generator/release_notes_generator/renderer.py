"""Render release notes sections into tyk-docs markdown/MDX format.

Uses the modern MDX component format:
- <AccordionGroup> / <Accordion title='...'> for changelog entries
- <a id="..."> for anchors
- <Note> for callouts
"""

from __future__ import annotations

from release_notes_generator.config import get_product_config
from release_notes_generator.models import ChangelogEntry, ReleaseSection


def render_release_section(section: ReleaseSection, release_highlights: str = "", is_new_minor: bool = False) -> str:
    parts: list[str] = []

    if is_new_minor:
        parts.append(f"## {section.major_minor} Release Notes ")
        parts.append("")

    parts.append(f"### {section.version} Release Notes ")
    parts.append("")
    parts.append(f"#### Release Date {section.release_date}")
    parts.append("")

    # Release Highlights.
    parts.append("#### Release Highlights")
    parts.append("")
    if release_highlights:
        parts.append(release_highlights.replace("VERSION", section.version))
    else:
        parts.append(
            "This release focuses mainly on bug fixes. "
            f"For a comprehensive list of changes, please refer to the detailed [changelog](#Changelog-v{section.version}) below."
        )
    parts.append("")

    # Breaking Changes.
    parts.append("#### Breaking Changes")
    parts.append("")
    if section.breaking_changes:
        for e in section.breaking_changes:
            desc = e.breaking_description or e.detail_text
            parts.append(f"- **{e.summary_line}**: {desc}")
        parts.append("")
    else:
        parts.append("There are no breaking changes in this release.")
        parts.append("")

    # Dependencies.
    parts.append("#### Dependencies")
    parts.append(f'<a id="dependencies-{section.version}"></a>')
    parts.append("")
    parts.append(_render_dependencies_placeholder(section))
    parts.append("")

    # Deprecations.
    parts.append("#### Deprecations")
    parts.append("")
    parts.append("There are no deprecations in this release.")
    parts.append("")

    # Upgrade Instructions.
    parts.append("#### Upgrade instructions")
    parts.append(f'<a id="upgrade-{section.version}"></a>')
    parts.append("")
    parts.append(f"If you are upgrading to {section.version}, please follow the detailed [upgrade instructions](#upgrading-tyk).")
    parts.append("")

    # Downloads.
    parts.append("#### Downloads")
    parts.append("")
    pc = get_product_config(section.product)
    if pc.docker:
        parts.append(f"- [Docker Image to pull](https://hub.docker.com/r/{pc.docker}/tags?page=&page_size=&ordering=&name=v{section.version})")
        parts.append(f"  - ```bash")
        parts.append(f"    docker pull {pc.docker}:v{section.version}")
        parts.append(f"    ```")
    parts.append("- Helm charts")
    parts.append(f'  - [tyk-charts](/developer-support/release-notes/helm-chart)')
    parts.append("")
    if pc.source_repo:
        parts.append(f"- [Source code tarball for OSS projects](https://github.com/{pc.source_repo}/releases)")
        parts.append("")

    # Changelog.
    parts.append("#### Changelog")
    parts.append(f'<a id="Changelog-v{section.version}" data-scroll-offset></a>')
    parts.append("")
    parts.append(_render_changelog(section))

    return "\n".join(parts)


def _render_changelog(section: ReleaseSection) -> str:
    """Render changelog using AccordionGroup/Accordion MDX components."""
    parts: list[str] = []

    categories = [
        ("Added", section.added),
        ("Changed", section.changed),
        ("Fixed", section.fixed),
        ("Security Fixes", section.security_fixes),
    ]

    for category_name, entries in categories:
        if not entries:
            continue
        parts.append(f"##### {category_name}")
        parts.append("")
        parts.append("<AccordionGroup>")
        parts.append("")
        for entry in entries:
            # Escape single quotes in title for MDX attribute.
            title = entry.summary_line.replace("'", "\\'")
            parts.append(f"<Accordion title='{title}'>")
            parts.append(entry.detail_text)
            parts.append("</Accordion>")
            parts.append("")
        parts.append("</AccordionGroup>")
        parts.append("")

    if not any(entries for _, entries in categories):
        parts.append("No changes in this release.")
        parts.append("")

    return "\n".join(parts)


def _render_dependencies_placeholder(section: ReleaseSection) -> str:
    """Render dependencies section with TODO placeholders."""
    return f"""| {section.product_label} Version | Recommended Releases | Backwards Compatibility |
|--------|-------------------|-------------|
| {section.version} | MDCB vX.Y.Z       | MDCB vX.Y.Z |
|        | Operator vX.Y.Z   | Operator vX.Y |
|        | Sync vX.Y.Z       | Sync vX.Y.Z |
|        | Helm Chart vX.Y   | Helm all versions |
|        | EDP vX.Y.Z        | EDP all versions |
|        | Pump vX.Y.Z       | Pump all versions |
|        | TIB (if using standalone) vX.Y.Z | TIB all versions |

##### 3rd Party Dependencies & Tools
<a id="3rdPartyTools-v{section.version}"></a>

| Third Party Dependency | Tested Versions | Compatible Versions | Comments |
| ---------------------- | --------------- | ------------------- | -------- |
| [GoLang](https://go.dev/dl/)          | X.YZ | X.YZ | [Go plugins](/api-management/plugins/golang) must be built using Go X.YZ |
| [Redis](https://redis.io/download/)   | 6.x, 7.x    |  6.x, 7.x    | |
| [Valkey](https://valkey.io/download/) | 8.0.x, 8.1.x    | 7.2.x, 8.0.x, 8.1.x    | |
| [MongoDB](https://www.mongodb.com/try/download/community)  | 6, 7, 8  | 5, 6, 7, 8  | |
| [DocumentDB](https://aws.amazon.com/documentdb/)  | 4, 5  | 4, 5  | |
| [PostgreSQL](https://www.postgresql.org/download/) | 13.x - 17.x | 13.x - 17.x  | |
| [OpenAPI Specification](https://spec.openapis.org/oas/v3.1.2.html) | v3.1.x | v3.1.x | Supported by [Tyk OAS](/api-management/gateway-config-tyk-oas)|

Given the potential time difference between your upgrade and the release of this version, we recommend users verify the ongoing support of third-party dependencies they install, as their status may have changed since the release."""
