import textwrap
from pathlib import Path
import pytest
from release_notes_generator.file_inserter import insert_release_section

@pytest.fixture
def tmp_rn(tmp_path):
    p = tmp_path / "gateway.mdx"
    p.write_text(textwrap.dedent("""\
        ---
        title: Tyk Gateway Release Notes
        ---
        ## Support Lifetime
        Our minor releases are supported until our next minor comes out.
        ---
        ## 5.7 Release Notes
        ### 5.7.2 Release Notes
        #### Release Date 19 February 2025
        ---
        ### 5.7.1 Release Notes
        #### Release Date 31 December 2024
        ---
        ## Further Information
    """))
    return p

class TestNewMinor:
    def test_before_existing(self, tmp_rn):
        r = insert_release_section(tmp_rn, "## 5.8 Release Notes\n\n### 5.8.0\n\nNew.", "5.8.0")
        assert r.index("## 5.8 Release Notes") < r.index("## 5.7 Release Notes")
    def test_preserves(self, tmp_rn):
        r = insert_release_section(tmp_rn, "## 5.8\n\nNew.", "5.8.0")
        assert "## 5.7 Release Notes" in r and "### 5.7.2" in r and "## Further Information" in r

class TestPatch:
    def test_before_existing(self, tmp_rn):
        r = insert_release_section(tmp_rn, "### 5.7.3 Release Notes\n\nPatch.", "5.7.3")
        assert r.index("### 5.7.3") < r.index("### 5.7.2")
    def test_preserves(self, tmp_rn):
        r = insert_release_section(tmp_rn, "### 5.7.3\n\nPatch.", "5.7.3")
        assert "### 5.7.2" in r and "### 5.7.1" in r

class TestEdge:
    def test_missing(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            insert_release_section(tmp_path / "x.mdx", "c", "5.8.0")
