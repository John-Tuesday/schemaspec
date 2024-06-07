import doctest
import unittest

from schemaspec import metafields


def load_tests(
    loader: unittest.TestLoader,
    tests,
    pattern,
) -> unittest.TestSuite:
    tests.addTests(doctest.DocTestSuite(metafields))
    return tests


if __name__ == "__main__":
    unittest.main()
