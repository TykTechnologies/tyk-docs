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


class TestRewriteSwaggerDownloadLinks(unittest.TestCase):
    def setUp(self):
        self.merger = DocsMerger()

    def test_rewrite_swagger_download_links_nightly_to_versioned(self):
        content = '<ButtonLeft href="https://raw.githubusercontent.com/TykTechnologies/tyk-docs/refs/heads/production/swagger/nightly/dashboard-swagger.yml" color="green" content="Download Swagger" />'
        result = self.merger.rewrite_swagger_download_links(content, "5.11")
        expected = '<ButtonLeft href="https://raw.githubusercontent.com/TykTechnologies/tyk-docs/refs/heads/production/swagger/5.11/dashboard-swagger.yml" color="green" content="Download Swagger" />'
        self.assertEqual(result, expected)

    def test_rewrite_swagger_download_links_main_branch_identity_broker(self):
        content = '<ButtonLeft href="https://raw.githubusercontent.com/TykTechnologies/tyk-docs/refs/heads/main/swagger/identity-broker-swagger.yml" color="green" content="Download Swagger" />'
        result = self.merger.rewrite_swagger_download_links(content, "5.11")
        expected = '<ButtonLeft href="https://raw.githubusercontent.com/TykTechnologies/tyk-docs/refs/heads/production/swagger/5.11/identity-broker-swagger.yml" color="green" content="Download Swagger" />'
        self.assertEqual(result, expected)

    def test_rewrite_swagger_download_links_yaml_extension(self):
        content = '<ButtonLeft href="https://raw.githubusercontent.com/TykTechnologies/tyk-docs/refs/heads/production/swagger/nightly/enterprise-developer-portal-swagger.yaml" color="green" content="Download Swagger" />'
        result = self.merger.rewrite_swagger_download_links(content, "5.10")
        expected = '<ButtonLeft href="https://raw.githubusercontent.com/TykTechnologies/tyk-docs/refs/heads/production/swagger/5.10/enterprise-developer-portal-swagger.yaml" color="green" content="Download Swagger" />'
        self.assertEqual(result, expected)

    def test_rewrite_swagger_download_links_json_extension(self):
        content = 'https://raw.githubusercontent.com/TykTechnologies/tyk-docs/refs/heads/production/swagger/nightly/spec.json'
        result = self.merger.rewrite_swagger_download_links(content, "5.11")
        expected = 'https://raw.githubusercontent.com/TykTechnologies/tyk-docs/refs/heads/production/swagger/5.11/spec.json'
        self.assertEqual(result, expected)

    def test_rewrite_swagger_download_links_from_existing_version(self):
        content = '<ButtonLeft href="https://raw.githubusercontent.com/TykTechnologies/tyk-docs/refs/heads/production/swagger/5.10/dashboard-swagger.yml" color="green" content="Download Swagger" />'
        result = self.merger.rewrite_swagger_download_links(content, "5.11")
        expected = '<ButtonLeft href="https://raw.githubusercontent.com/TykTechnologies/tyk-docs/refs/heads/production/swagger/5.11/dashboard-swagger.yml" color="green" content="Download Swagger" />'
        self.assertEqual(result, expected)

    def test_rewrite_swagger_download_links_for_nightly_version(self):
        content = '<ButtonLeft href="https://raw.githubusercontent.com/TykTechnologies/tyk-docs/refs/heads/production/swagger/nightly/gateway-swagger.yml" color="green" content="Download Swagger" />'
        result = self.merger.rewrite_swagger_download_links(content, "nightly")
        expected = '<ButtonLeft href="https://raw.githubusercontent.com/TykTechnologies/tyk-docs/refs/heads/production/swagger/nightly/gateway-swagger.yml" color="green" content="Download Swagger" />'
        self.assertEqual(result, expected)

    def test_rewrite_swagger_download_links_unrelated_urls_unchanged(self):
        content = "https://raw.githubusercontent.com/TykTechnologies/tyk/refs/heads/master/apidef/oas/schema/3.0.json"
        result = self.merger.rewrite_swagger_download_links(content, "5.11")
        self.assertEqual(result, content)

    def test_rewrite_swagger_download_links_multiple_links(self):
        content = (
            "Dashboard: https://raw.githubusercontent.com/TykTechnologies/tyk-docs/refs/heads/production/swagger/nightly/dashboard-swagger.yml\n"
            "Gateway: https://raw.githubusercontent.com/TykTechnologies/tyk-docs/refs/heads/production/swagger/nightly/gateway-swagger.yml"
        )
        result = self.merger.rewrite_swagger_download_links(content, "5.11")
        self.assertIn("swagger/5.11/dashboard-swagger.yml", result)
        self.assertIn("swagger/5.11/gateway-swagger.yml", result)


if __name__ == "__main__":
    unittest.main()
