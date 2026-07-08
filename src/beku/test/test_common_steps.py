"""Tests for the common-steps feature: files in a common directory are rendered into every test case."""

import tempfile
import unittest
from os import makedirs, path

from beku.kuttl import TestCase


def _write(file_path: str, content: str) -> None:
    makedirs(path.dirname(file_path), exist_ok=True)
    with open(file_path, encoding="utf8", mode="w") as stream:
        stream.write(content)


class TestCommonSteps(unittest.TestCase):
    def test_common_dir_rendered_into_test_case(self):
        with tempfile.TemporaryDirectory() as tmp:
            template_dir = path.join(tmp, "templates")
            common_dir = path.join(tmp, "commons")
            target_dir = path.join(tmp, "_work")

            # A test with its own step, and a plain + templated common file.
            _write(path.join(template_dir, "mytest", "00-install.yaml"), "step\n")
            _write(path.join(common_dir, "99-teardown.yaml"), "teardown\n")
            _write(path.join(common_dir, "50-note.txt.j2"), "ns={{ NAMESPACE }}\n")

            TestCase(name="mytest", values={}).expand(template_dir, target_dir, "kuttl-fixed", common_dir)

            tc_dir = path.join(target_dir, "mytest", "mytest")
            # the test's own step is present
            self.assertTrue(path.isfile(path.join(tc_dir, "00-install.yaml")))
            # the common plain file is present
            self.assertTrue(path.isfile(path.join(tc_dir, "99-teardown.yaml")))
            # the common template is rendered (suffix stripped, NAMESPACE substituted)
            rendered = path.join(tc_dir, "50-note.txt")
            self.assertTrue(path.isfile(rendered))
            with open(rendered, encoding="utf8") as stream:
                self.assertIn("ns=kuttl-fixed", stream.read())

    def test_test_own_file_wins_on_collision(self):
        with tempfile.TemporaryDirectory() as tmp:
            template_dir = path.join(tmp, "templates")
            common_dir = path.join(tmp, "shared")
            target_dir = path.join(tmp, "_work")

            # Same file name in the test and in the shared dir, with different content.
            _write(path.join(template_dir, "mytest", "10-check.yaml"), "TEST-OWN\n")
            _write(path.join(common_dir, "10-check.yaml"), "SHARED\n")

            TestCase(name="mytest", values={}).expand(template_dir, target_dir, "kuttl-fixed", common_dir)

            # The test's own file must win; the shared file must not clobber it.
            with open(path.join(target_dir, "mytest", "mytest", "10-check.yaml"), encoding="utf8") as stream:
                self.assertEqual("TEST-OWN\n", stream.read())

    def test_missing_common_dir_is_skipped(self):
        with tempfile.TemporaryDirectory() as tmp:
            template_dir = path.join(tmp, "templates")
            target_dir = path.join(tmp, "_work")
            _write(path.join(template_dir, "mytest", "00-install.yaml"), "step\n")

            # Non-existent common dir must not raise and must not add anything.
            TestCase(name="mytest", values={}).expand(
                template_dir, target_dir, "kuttl-fixed", path.join(tmp, "does-not-exist")
            )

            tc_dir = path.join(target_dir, "mytest", "mytest")
            self.assertTrue(path.isfile(path.join(tc_dir, "00-install.yaml")))
            self.assertFalse(path.isfile(path.join(tc_dir, "99-teardown.yaml")))

    def test_no_common_dir_argument_is_backwards_compatible(self):
        with tempfile.TemporaryDirectory() as tmp:
            template_dir = path.join(tmp, "templates")
            target_dir = path.join(tmp, "_work")
            _write(path.join(template_dir, "mytest", "00-install.yaml"), "step\n")

            # Old call signature (no common_dir) keeps working.
            TestCase(name="mytest", values={}).expand(template_dir, target_dir, "kuttl-fixed")

            self.assertTrue(path.isfile(path.join(target_dir, "mytest", "mytest", "00-install.yaml")))


if __name__ == "__main__":
    unittest.main()
