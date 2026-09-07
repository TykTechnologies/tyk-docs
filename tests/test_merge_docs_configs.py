import unittest
from scripts.merge_docs_configs import DocsMerger


class TestRewriteInternalLinks(unittest.TestCase):
    def setUp(self):
        self.merger = DocsMerger()
        self.merger_with_subfolder = DocsMerger(subfolder="docs")

    def test_markdown_anchor_links_not_prefixed_nightly(self):
        content = "[changelog](#Changelog-v2.2.2)"
        result = self.merger.rewrite_internal_links(content, "nightly", False)
        self.assertEqual(result, "[changelog](#Changelog-v2.2.2)")

    def test_markdown_anchor_links_with_whitespace_not_prefixed(self):
        content = "[changelog]( #Changelog-v2.2.2 )"
        result = self.merger.rewrite_internal_links(content, "nightly", False)
        self.assertEqual(result, "[changelog]( #Changelog-v2.2.2 )")

    def test_html_anchor_href_not_prefixed(self):
        content = '<a href="#Changelog-v2.2.2">Changelog</a>'
        result = self.merger.rewrite_internal_links(content, "nightly", False)
        self.assertEqual(result, '<a href="#Changelog-v2.2.2">Changelog</a>')

    def test_html_anchor_href_with_whitespace_not_prefixed(self):
        content = '<a href=" #Changelog-v2.2.2 ">Changelog</a>'
        result = self.merger.rewrite_internal_links(content, "nightly", False)
        self.assertEqual(result, '<a href=" #Changelog-v2.2.2 ">Changelog</a>')

    def test_card_component_anchor_not_prefixed(self):
        content = '<Card href="#features">Features</Card>'
        result = self.merger.rewrite_internal_links(content, "nightly", False)
        self.assertEqual(result, '<Card href="#features">Features</Card>')

    def test_root_fragment_rewritten_to_anchor_not_prefixed(self):
        content = "[root fragment](/#overview)\nhref=\"/#overview\""
        result = self.merger.rewrite_internal_links(content, "nightly", False)
        self.assertIn("[root fragment](#overview)", result)
        self.assertIn('href="#overview"', result)

    def test_relative_markdown_link_with_anchor_is_prefixed(self):
        content = "[another](some-page#section)"
        result = self.merger.rewrite_internal_links(content, "nightly", False)
        self.assertEqual(result, "[another](/nightly/some-page#section)")

    def test_absolute_markdown_link_is_prefixed(self):
        content = "[abs](/docs/foo)"
        result = self.merger.rewrite_internal_links(content, "nightly", False)
        self.assertEqual(result, "[abs](/nightly/docs/foo)")

    def test_card_relative_link_is_prefixed(self):
        content = '<Card href="docs/features">Features</Card>'
        result = self.merger.rewrite_internal_links(content, "nightly", False)
        self.assertEqual(result, '<Card href="/nightly/docs/features">Features</Card>')

    def test_external_and_mailto_links_unchanged(self):
        content = "[ext](https://example.com)\n[mail](mailto:test@example.com)"
        result = self.merger.rewrite_internal_links(content, "nightly", False)
        self.assertEqual(content, result)

    def test_subfolder_preserves_anchors(self):
        content = "[changelog](#Changelog-v2.2.2)\n<a href=\"#Changelog-v2.2.2\">Changelog</a>\n[page](/page)"
        result = self.merger_with_subfolder.rewrite_internal_links(content, "nightly", False)
        self.assertIn("[changelog](#Changelog-v2.2.2)", result)
        self.assertIn('<a href="#Changelog-v2.2.2">Changelog</a>', result)
        self.assertIn("[page](/docs/nightly/page)", result)


if __name__ == "__main__":
    unittest.main()
