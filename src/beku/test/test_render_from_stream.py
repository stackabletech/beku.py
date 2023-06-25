import textwrap
import unittest

from beku.kuttl import renderer_from_stream, EffectiveTestSuite, TestCase


class TestRenderFromStream(unittest.TestCase):

    def test_default_test_suite(self):
        fixture = textwrap.dedent("""
            ---
            dimensions:
              - name: druid
                values:
                  - 24.0.0-stackable0.0.0-dev
            tests:
              - name: smoke
                dimensions:
                  - druid""")
        ets = renderer_from_stream(fixture)
        expected = EffectiveTestSuite(name='default',
                                      test_cases=[TestCase(name='smoke',
                                                           values={'druid': '24.0.0-stackable0.0.0-dev'})])
        self.assertEqual(
            expected, ets[0], "No select, patch implicitly selected tests smoke")

    def test_patch_implicit_select(self):
        fixture = textwrap.dedent("""
            ---
            dimensions:
              - name: druid
                values:
                  - 24.0.0-stackable0.0.0-dev
                  - 26.0.0-stackable0.0.0-dev
            tests:
              - name: smoke
                dimensions:
                  - druid
            suites:
              - name: latest
                patch:
                  - test: smoke
                    dimensions:
                      - name: druid
                        expr: first""")
        ets = renderer_from_stream(fixture)
        expected = EffectiveTestSuite(name='latest',
                                      test_cases=[TestCase(name='smoke',
                                                           values={'druid': '24.0.0-stackable0.0.0-dev'})])
        self.assertEqual(
            expected, ets[0], "No select, patch implicitly selected tests smoke")

    def test_patch_ignores_test_that_was_not_selected(self):
        fixture = textwrap.dedent("""
            ---
            dimensions:
              - name: druid
                values:
                  - 24.0.0-stackable0.0.0-dev
                  - 26.0.0-stackable0.0.0-dev
            tests:
              - name: smoke
                dimensions:
                  - druid
              - name: resources
                dimensions:
                  - druid
            suites:
              - name: first
                select:
                  - resources
                patch:
                  - test: smoke
                    dimensions:
                      - name: druid
                        expr: first""")

        ets = renderer_from_stream(fixture)

        self.assertEqual(["resources"], list(dict.fromkeys([tc.name for tc in ets[0].test_cases])),
                         "Only the [resources] test definition was selected.")

    def test_patch_the_same_dimension_twice(self):
        fixture = textwrap.dedent("""
            ---
            dimensions:
              - name: druid
                values:
                  - 24.0.0-stackable0.0.0-dev
                  - 25.0.0-stackable0.0.0-dev
                  - 26.0.0-stackable0.0.0-dev
            tests:
              - name: smoke
                dimensions:
                  - druid
            suites:
              - name: two-patches-on-the-same-test
                patch:
                  - test: smoke
                    dimensions:
                      - name: druid
                        expr: first
                      - name: druid
                        expr: last
        """)
        ets = renderer_from_stream(fixture)
        expected = EffectiveTestSuite(name='two-patches-on-the-same-test',
                                      test_cases=[TestCase(name='smoke',
                                                           values={'druid': '26.0.0-stackable0.0.0-dev'})])
        self.assertEqual(expected, ets[0], "Last patch wins")

    def test_patch_the_same_test_twice(self):
        fixture = textwrap.dedent("""
            ---
            dimensions:
              - name: druid
                values:
                  - 24.0.0-stackable0.0.0-dev
                  - 25.0.0-stackable0.0.0-dev
                  - 26.0.0-stackable0.0.0-dev
            tests:
              - name: smoke
                dimensions:
                  - druid
            suites:
              - name: two-patches-on-the-same-test
                patch:
                  - test: smoke
                    dimensions:
                      - name: druid
                        expr: first
                  - test: smoke
                    dimensions:
                      - name: druid
                        expr: last
        """)
        ets = renderer_from_stream(fixture)
        expected = EffectiveTestSuite(name='two-patches-on-the-same-test',
                                      test_cases=[TestCase(name='smoke',
                                                           values={'druid': '24.0.0-stackable0.0.0-dev'})])
        self.assertEqual(
            expected, ets[0], "First patch select 24.0.0 and the second has only one value to choose from")

    def test_patch_str_expression(self):
        fixture = textwrap.dedent("""
            ---
            dimensions:
              - name: druid
                values:
                  - 24.0.0-stackable0.0.0-dev
                  - 25.0.0-stackable0.0.0-dev
                  - 26.0.0-stackable0.0.0-dev
            tests:
              - name: smoke
                dimensions:
                  - druid
            suites:
              - name: select-27.0.0
                patch:
                  - test: smoke
                    dimensions:
                      - name: druid
                        expr: "27.0.0"
        """)
        ets = renderer_from_stream(fixture)
        expected = EffectiveTestSuite(name='select-27.0.0',
                                      test_cases=[TestCase(name='smoke',
                                                           values={'druid': '27.0.0'})])
        self.assertEqual(expected, ets[0], "String expression works")

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
        self.assertEqual(3, len(ets[0].test_cases),
                         "The [latest] test suite has 3 test cases.")
        self.assertEqual(["smoke", "resources"], list(dict.fromkeys([tc.name for tc in ets[0].test_cases])),
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
        self.assertEqual(2, len(ets[0].test_cases),
                         "The [latest] test suite has 2 test cases.")
        self.assertEqual(["smoke", "resources"], list(dict.fromkeys([tc.name for tc in ets[0].test_cases])),
                         "Two test definitions were selected.")

    def test_multiple_patches(self):
        fixture = textwrap.dedent("""
            ---
            dimensions:
              - name: druid
                values:
                  - 24.0.0-stackable0.0.0-dev
                  - 26.0.0-stackable0.0.0-dev
              - name: zookeeper
                values:
                  - 3.7.0-stackable0.0.0-dev
                  - 3.8.0-stackable0.0.0-dev
              - name: openshift
                values:
                  - "false"
            tests:
              - name: smoke
                dimensions:
                  - druid
                  - zookeeper
                  - openshift
            suites:
              - name: openshift
                patch:
                  - dimensions:
                      - expr: last
                  -  dimensions:
                      - name: openshift
                        expr: "true"
            """)
        ets = renderer_from_stream(fixture)
        expected = EffectiveTestSuite(name='openshift',
                                      test_cases=[TestCase(name='smoke',
                                                           values={'druid': '26.0.0-stackable0.0.0-dev',
                                                                   'openshift': 'true',
                                                                   'zookeeper': '3.8.0-stackable0.0.0-dev'})])

        self.assertEqual(expected, ets[0])


if __name__ == '__main__':
    unittest.main()
