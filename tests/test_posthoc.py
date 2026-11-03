"""The post hoc test-path rule: a directory segment containing "test", not the file name."""
import unittest

from long_method_slim_study import posthoc


class PostHocTest(unittest.TestCase):

    def test_test_path_rule(self):
        self.assertTrue(posthoc.is_test_path("guava-tests/benchmark/com/google/Foo.java"))
        self.assertTrue(posthoc.is_test_path("a/internalClusterTest/Foo.java"))
        self.assertTrue(posthoc.is_test_path("src/androidTest/java/Foo.java"))
        self.assertFalse(posthoc.is_test_path("src/main/java/Foo.java"))
        self.assertFalse(posthoc.is_test_path("src/main/java/TestRunner.java"))  # the file name does not count
        self.assertFalse(posthoc.is_test_path("Foo.java"))


if __name__ == "__main__":
    unittest.main()
