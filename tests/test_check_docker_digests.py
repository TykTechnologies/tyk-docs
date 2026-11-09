import os
import tempfile
import unittest
from unittest import mock

from scripts import check_docker_digests as cdd

D1 = "a" * 64
D2 = "b" * 64


def pull(image, tag, digest):
    return f"    docker pull {image}:{tag}@sha256:{digest}\n"


class CheckDockerDigestsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def write(self, name, content):
        path = os.path.join(self.tmp.name, name)
        with open(path, "w") as f:
            f.write(content)
        return path

    def test_distinct_digests_pass(self):
        f = self.write("tib.mdx", pull("tykio/tib", "v1.8.4", D1) + pull("tykio/tib", "v1.8.3", D2))
        self.assertEqual(cdd.main([f]), 0)

    def test_same_digest_for_two_versions_fails(self):
        f = self.write("tib.mdx", pull("tykio/tib", "v1.8.4", D1) + pull("tykio/tib", "v1.8.1", D1))
        errors = cdd.check_duplicates(cdd.find_pulls([f]))
        self.assertEqual(len(errors), 1)
        self.assertIn("tykio/tib:v1.8.4", errors[0])
        self.assertIn("tykio/tib:v1.8.1", errors[0])
        self.assertEqual(cdd.main([f]), 1)

    def test_same_ref_repeated_across_files_passes(self):
        a = self.write("a.mdx", pull("tykio/tib", "v1.8.4", D1))
        b = self.write("b.mdx", pull("tykio/tib", "v1.8.4", D1))
        self.assertEqual(cdd.main([a, b]), 0)

    def test_short_digest_fails(self):
        f = self.write("a.mdx", pull("tykio/tib", "v1.8.4", "abc123"))
        self.assertEqual(cdd.main([f]), 1)

    def test_unpinned_pull_ignored(self):
        f = self.write("a.mdx", "docker pull tykio/tib:v1.7.0\n")
        self.assertEqual(cdd.find_pulls([f]), [])

    def test_registry_mismatch_missing_tag_and_network_error(self):
        f = self.write("a.mdx",
                       pull("tykio/ok", "v1", D1)
                       + pull("tykio/wrong", "v1", D1.replace("a", "c", 1))
                       + pull("tykio/missing", "v1", D2)
                       + pull("tykio/down", "v1", D2.replace("b", "c", 1))
                       + pull("ghcr.io/tyk/x", "v1", D2.replace("b", "d", 1)))
        served = {"tykio/ok": "sha256:" + D1, "tykio/wrong": "sha256:" + D1, "tykio/missing": None}

        def fake(session, image, tag):
            if image == "tykio/down":
                raise ConnectionError("boom")
            return served[image]

        with mock.patch.object(cdd, "registry_digest", side_effect=fake):
            errors, warnings = cdd.check_registry(cdd.find_pulls([f]), session=None)
        self.assertEqual(len(errors), 2)
        self.assertIn("tykio/wrong:v1", errors[0])
        self.assertIn("does not exist", errors[1])
        self.assertEqual(len(warnings), 2)


if __name__ == "__main__":
    unittest.main()
