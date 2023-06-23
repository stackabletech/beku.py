import textwrap
import unittest

from beku.testsuite import renderer_from_stream


class TestSum(unittest.TestCase):
    def test_resolve_explicit_select(self):
        fixture = textwrap.dedent("""
            ---
            dimensions:
              - name: druid
                values:
                  - 0.23.0-stackable0.0.0-dev
                  - 24.0.0-stackable0.0.0-dev
                  - 26.0.0-stackable0.0.0-dev
              - name: druid-latest
                values:
                  - 26.0.0-stackable0.0.0-dev
              - name: zookeeper
                values:
                  - 3.7.0-stackable0.0.0-dev
                  - 3.8.0-stackable0.0.0-dev
              - name: zookeeper-latest
                values:
                  - 3.8.0-stackable0.0.0-dev
            tests:
              - name: smoke
                dimensions:
                  - druid
                  - zookeeper
              - name: resources
                dimensions:
                  - druid-latest
                  - zookeeper-latest
            suites:
              - name: latest
                select:
                  - smoke
                  - resources
                patch:
                  - test: smoke
                    dimensions:
                      - name: druid
                        expr: last""")
        ets = renderer_from_stream(fixture)
        # pprint(ets[0].test_cases)
        self.assertEqual(["default", "latest"], [
                         e.name for e in ets], "Two effective test suite resolved.")
        self.assertEqual(7, len(ets[0].test_cases),
                         "The [default] test suite has 7 test cases.")
        self.assertEqual(3, len(ets[1].test_cases),
                         "The [latest] test suite has 3 test cases.")
        self.assertEqual(["smoke", "resources"], list(dict.fromkeys([tc.name for tc in ets[1].test_cases])),
                         "Two test definitions were selected.")

    def test_resolve_select_all(self):
        fixture = textwrap.dedent("""
            ---
            dimensions:
              - name: druid
                values:
                  - 0.23.0-stackable0.0.0-dev
                  - 24.0.0-stackable0.0.0-dev
                  - 26.0.0-stackable0.0.0-dev
              - name: druid-latest
                values:
                  - 26.0.0-stackable0.0.0-dev
              - name: zookeeper
                values:
                  - 3.7.0-stackable0.0.0-dev
                  - 3.8.0-stackable0.0.0-dev
              - name: zookeeper-latest
                values:
                  - 3.8.0-stackable0.0.0-dev
            tests:
              - name: smoke
                dimensions:
                  - druid
                  - zookeeper
              - name: resources
                dimensions:
                  - druid
                  - zookeeper-latest
            suites:
              - name: latest
                patch:
                  - dimensions:
                      - expr: last""")
        ets = renderer_from_stream(fixture)
        # pprint(ets[0].test_cases)
        self.assertEqual(["default", "latest"], [
                         e.name for e in ets], "Two effective test suite resolved.")
        self.assertEqual(9, len(ets[0].test_cases),
                         "The [default] test suite has 9 test cases.")
        self.assertEqual(2, len(ets[1].test_cases),
                         "The [latest] test suite has 2 test cases.")
        self.assertEqual(["smoke", "resources"], list(dict.fromkeys([tc.name for tc in ets[0].test_cases])),
                         "Two test definitions were selected.")


if __name__ == '__main__':
    unittest.main()
