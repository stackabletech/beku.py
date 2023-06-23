import textwrap
import unittest
from pprint import pprint

from beku.testsuite import renderer_from_stream


class TestSum(unittest.TestCase):
    def test_load(self):
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
                patch:
                  - test: smoke
                    dimensions:
                      - name: druid
                        expr: last""")
        ets = renderer_from_stream(fixture)
        pprint(ets)


if __name__ == '__main__':
    unittest.main()
