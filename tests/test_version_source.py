import unittest


class TestVersionFormatting(unittest.TestCase):
    def setUp(self) -> None:
        from hatch_mpt_versioning.version_source import _format_version, _parse_describe

        self._format_version = _format_version
        self._parse_describe = _parse_describe
        self.tag_regex = r"^(?:v)?(?P<version>\d+(?:\.\d+)*)$"

    def test_exact_tag_clean(self):
        desc = self._parse_describe("1.0.0-0-g4cdc9aa")
        self.assertEqual(self._format_version(desc, self.tag_regex), "1.0.0")

    def test_tag_one_commit_ahead(self):
        desc = self._parse_describe("1.0.0-1-g4cdc9aa")
        self.assertEqual(self._format_version(desc, self.tag_regex), "1.0.1+g4cdc9aa")

    def test_tag_many_commits_ahead(self):
        desc = self._parse_describe("1.0.0-12-g4cdc9aa")
        self.assertEqual(self._format_version(desc, self.tag_regex), "1.0.12+g4cdc9aa")

    def test_dirty_appends_dirty(self):
        desc = self._parse_describe("1.0.0-1-g4cdc9aa-dirty")
        self.assertEqual(self._format_version(desc, self.tag_regex), "1.0.1+g4cdc9aa.dirty")

    def test_dirty_on_tag(self):
        desc = self._parse_describe("1.0.0-0-g4cdc9aa-dirty")
        self.assertEqual(self._format_version(desc, self.tag_regex), "1.0.0+g4cdc9aa.dirty")

    def test_no_local_version_one_commit_ahead(self):
        desc = self._parse_describe("1.0.0-1-g4cdc9aa")
        self.assertEqual(
            self._format_version(desc, self.tag_regex, local_version=False), "1.0.1"
        )

    def test_no_local_version_dirty(self):
        desc = self._parse_describe("1.0.0-1-g4cdc9aa-dirty")
        self.assertEqual(
            self._format_version(desc, self.tag_regex, local_version=False), "1.0.1"
        )

    def test_no_local_version_dirty_on_tag(self):
        desc = self._parse_describe("1.0.0-0-g4cdc9aa-dirty")
        self.assertEqual(
            self._format_version(desc, self.tag_regex, local_version=False), "1.0.0"
        )


if __name__ == "__main__":
    unittest.main()

