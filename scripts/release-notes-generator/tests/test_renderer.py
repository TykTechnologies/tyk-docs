"""Tests for the renderer module — MDX AccordionGroup format."""

from release_notes_generator.models import ChangelogEntry, ReleaseSection
from release_notes_generator.renderer import render_release_section


def _e(key="TT-1", cat="Fixed", summary="Fixed bug", detail="Done.", breaking=False):
    return ChangelogEntry(ticket_key=key, category=cat, summary_line=summary, detail_text=detail, is_breaking=breaking, breaking_description="Break." if breaking else None)


def _s(entries=None, version="5.8.0"):
    return ReleaseSection(version=version, release_date="24 March 2026", product="gateway", product_label="Gateway", entries=entries or [])


class TestRender:
    def test_version_header(self):
        assert "### 5.8.0 Release Notes" in render_release_section(_s())

    def test_release_date(self):
        assert "#### Release Date 24 March 2026" in render_release_section(_s())

    def test_no_breaking(self):
        assert "There are no breaking changes" in render_release_section(_s())

    def test_breaking(self):
        assert "Break." in render_release_section(_s([_e(breaking=True)]))

    def test_fixed_uses_accordion(self):
        r = render_release_section(_s([_e(cat="Fixed", summary="Fix")]))
        assert "##### Fixed" in r
        assert "<AccordionGroup>" in r
        assert "<Accordion title='Fix'>" in r
        assert "</AccordionGroup>" in r

    def test_added_uses_accordion(self):
        r = render_release_section(_s([_e(cat="Added", summary="New")]))
        assert "##### Added" in r
        assert "<Accordion title='New'>" in r

    def test_accordion_contains_detail(self):
        r = render_release_section(_s([_e(detail="Detail text here.")]))
        assert "Detail text here." in r

    def test_new_minor(self):
        assert "## 5.8 Release Notes" in render_release_section(_s(version="5.8.0"), is_new_minor=True)

    def test_patch_no_minor(self):
        assert "## 5.7 Release Notes" not in render_release_section(_s(version="5.7.3"))

    def test_docker(self):
        assert "docker pull tykio/tyk-gateway:v5.8.0" in render_release_section(_s([_e()]))

    def test_changelog_anchor(self):
        r = render_release_section(_s())
        assert '<a id="Changelog-v5.8.0" data-scroll-offset></a>' in r

    def test_dependencies_anchor(self):
        r = render_release_section(_s())
        assert '<a id="dependencies-5.8.0"></a>' in r

    def test_multiple_categories(self):
        r = render_release_section(_s([_e(key="1", cat="Added", summary="A"), _e(key="2", cat="Fixed", summary="F"), _e(key="3", cat="Changed", summary="C")]))
        assert "##### Added" in r and "##### Fixed" in r and "##### Changed" in r

    def test_single_quotes_escaped_in_title(self):
        r = render_release_section(_s([_e(summary="Fix for user's issue")]))
        assert "<Accordion title='Fix for user\\'s issue'>" in r
