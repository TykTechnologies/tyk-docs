import json
import os
import tempfile
import unittest

from scripts import check_release_data as crd

NOTES = """---
title: "TIB"
---

## 1.8 Release Notes

### 1.8.4 Release Notes

#### Release Date 29 October 2026

### 1.8.3 Release Notes

#### Release Date 22nd October 2026

## 1.7 Release Notes

### 1.7.3 Release Notes

#### Release Date 1 May 2026
"""


def component(**overrides):
    c = {
        "name": "Tyk Identity Broker",
        "latest": "1.8.4",
        "releaseNotesPath": "rn/tib",
        "latestData": {
            "name": "1.8.4",
            "docker": "https://hub.docker.com/r/tykio/tyk-identity-broker/tags?page=1&name=1.8.4",
            "tag": "https://github.com/TykTechnologies/tyk-identity-broker/releases/tag/v1.8.4",
        },
    }
    data = overrides.pop("latestData", {})
    c.update(overrides)
    c["latestData"].update(data)
    return c


class CheckReleaseDataTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        os.makedirs(os.path.join(self.tmp.name, "rn"))
        with open(os.path.join(self.tmp.name, "rn", "tib.mdx"), "w") as f:
            f.write(NOTES)

    def check(self, c):
        return crd.check_component(c, self.tmp.name)

    def test_matching_data_passes(self):
        self.assertEqual(self.check(component()), [])

    def test_stale_version_fails(self):
        c = component(latest="1.8.3", latestData={
            "name": "1.8.3",
            "docker": "https://hub.docker.com/r/tykio/tyk-identity-broker/tags?page=1&name=1.8.3",
            "tag": "https://github.com/TykTechnologies/tyk-identity-broker/releases/tag/v1.8.3"})
        errors = self.check(c)
        self.assertEqual(len(errors), 4)
        self.assertTrue(all("1.8.4" in e for e in errors))

    def test_lts(self):
        self.assertEqual(self.check(component(lts="1.7.3")), [])
        self.assertIn("newest release notes in that line are for 1.8.4", self.check(component(lts="1.8.3"))[0])
        self.assertIn("no release notes for 1.6.x", self.check(component(lts="1.6.0"))[0])

    def test_unversioned_links_ignored(self):
        c = component(latestData={"docker": "", "tag": "https://github.com/TykTechnologies/tyk-charts/releases"})
        self.assertEqual(self.check(c), [])

    def test_missing_notes_file(self):
        self.assertIn("does not exist", self.check(component(releaseNotesPath="rn/nope"))[0])

    def test_loads_inline_overview_data(self):
        os.makedirs(os.path.join(self.tmp.name, "developer-support", "release-notes"))
        path = os.path.join(self.tmp.name, "developer-support", "release-notes", "overview.mdx")
        with open(path, "w") as f:
            f.write("---\ntitle: x\n---\n\nexport const releaseData = "
                    + json.dumps({"opensource": [component()]}) + ";\n\n<Summary />\n")
        self.assertEqual(crd.main([self.tmp.name]), 0)


if __name__ == "__main__":
    unittest.main()
