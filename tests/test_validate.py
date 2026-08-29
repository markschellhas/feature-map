import unittest
from pathlib import Path

from featuremap.loader import all_slugs
from featuremap.validate import validate_map_file
from helpers import FEATURES, FeaturemapTestCase


class ValidateTests(FeaturemapTestCase):
    def test_valid_map_has_no_errors(self):
        slugs = all_slugs(FEATURES)
        errors, warnings = validate_map_file(FEATURES / "auth.yaml", slugs)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

    def test_broken_related_is_warning(self):
        slugs = all_slugs(FEATURES)
        errors, warnings = validate_map_file(FEATURES / "notifications.yaml", slugs)
        self.assertEqual(errors, [])
        self.assertTrue(any("does_not_exist" in item for item in warnings))

    def test_missing_notes_is_not_a_warning(self):
        path = self.tmpdir / "signup.yaml"
        path.write_text(
            "feature_name: signup\n"
            "purpose: Create an account.\n"
            "entry_points:\n  - src/app.py\n"
            "apps:\n  - api\n"
            "user_flow:\n  primary: Submit → account.\n"
            "related_features:\n  - auth (session after signup)\n",
            encoding="utf-8",
        )
        errors, warnings = validate_map_file(path, {"signup", "auth"})
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])


if __name__ == "__main__":
    unittest.main()
