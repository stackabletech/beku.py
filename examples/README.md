# Configuration Examples

This folder contains configuration examples for Beku.

## Test Suites

The folder `suites` contains an example on how to configure test suites.

The file `suites/test/test-definition.yaml` shows example configurations for two test suites:

    suites:
    - name: latest # this suite will set all dimension values to the latest (last) value
      patch:
      - dimensions:
        - expr: last
    - name: smoke # this suite will only select the smoke tests
      select:
      - smoke

The `latest` suite will execute all tests only with the latest versions of each dimension.
The `smoke` suite will expand only the `smoke` tests and ignore all others.

To select which suite to expand, use the --suite command line argument. For example:

    cd examples/suites
    rm -rf tests/_work
    beku --suite latest

will generate the test cases for the `latest` suite.
