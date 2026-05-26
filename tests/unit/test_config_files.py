"""
Tests for repository-level configuration files added in this PR:
  - .coderabbit.yaml  (CodeRabbit AI review configuration)
  - .presidiocli      (Presidio PII-detection configuration)

These tests parse each file as YAML and assert that the structure,
values, and security-relevant settings match the intended configuration.
No Django or database dependencies are required.
"""

import os
import unittest

import yaml

# Resolve paths relative to the repository root so the tests work
# regardless of the working directory from which pytest is launched.
REPO_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)
CODERABBIT_YAML_PATH = os.path.join(REPO_ROOT, ".coderabbit.yaml")
PRESIDIOCLI_PATH = os.path.join(REPO_ROOT, ".presidiocli")


def _load_yaml(path):
    """Return the parsed YAML document at *path*."""
    with open(path, "r") as fh:
        return yaml.safe_load(fh)


# ---------------------------------------------------------------------------
# Helper – loaded once per test class via setUpClass so we don't re-read
# the files for every individual test.
# ---------------------------------------------------------------------------


class CodeRabbitYamlTests(unittest.TestCase):
    """Validate the structure and values of .coderabbit.yaml."""

    @classmethod
    def setUpClass(cls):
        cls.config = _load_yaml(CODERABBIT_YAML_PATH)

    # ------------------------------------------------------------------
    # File-level / basic sanity
    # ------------------------------------------------------------------

    def test_file_exists(self):
        self.assertTrue(
            os.path.isfile(CODERABBIT_YAML_PATH),
            ".coderabbit.yaml must exist at the repository root",
        )

    def test_parses_as_valid_yaml(self):
        """The file must parse without errors and produce a dict."""
        self.assertIsInstance(self.config, dict)

    def test_top_level_keys_present(self):
        """The three top-level sections must all be present."""
        for key in ("language", "reviews", "chat"):
            self.assertIn(
                key,
                self.config,
                f"Top-level key '{key}' missing from .coderabbit.yaml",
            )

    # ------------------------------------------------------------------
    # language
    # ------------------------------------------------------------------

    def test_language_is_en_us(self):
        self.assertEqual(self.config["language"], "en-US")

    # ------------------------------------------------------------------
    # reviews – top-level fields
    # ------------------------------------------------------------------

    def test_reviews_section_is_dict(self):
        self.assertIsInstance(self.config["reviews"], dict)

    def test_reviews_profile_is_chill(self):
        self.assertEqual(self.config["reviews"]["profile"], "chill")

    def test_reviews_review_status_enabled(self):
        self.assertIs(self.config["reviews"]["review_status"], True)

    def test_reviews_review_details_disabled(self):
        self.assertIs(self.config["reviews"]["review_details"], False)

    def test_reviews_poem_disabled(self):
        self.assertIs(self.config["reviews"]["poem"], False)

    def test_reviews_prompt_for_ai_agents_disabled(self):
        self.assertIs(self.config["reviews"]["prompt_for_ai_agents"], False)

    def test_reviews_instructions_present(self):
        instructions = self.config["reviews"].get("instructions", "")
        self.assertTrue(
            instructions.strip(),
            "reviews.instructions must not be empty",
        )

    # ------------------------------------------------------------------
    # reviews.instructions – sensitive-data guardrails
    # ------------------------------------------------------------------

    def test_instructions_mention_redacted_placeholder(self):
        instructions = self.config["reviews"]["instructions"]
        self.assertIn(
            "[REDACTED]",
            instructions,
            "Instructions must direct CodeRabbit to use [REDACTED] for sensitive values",
        )

    def test_instructions_prohibit_api_keys(self):
        instructions = self.config["reviews"]["instructions"].lower()
        self.assertIn("api key", instructions)

    def test_instructions_prohibit_pii(self):
        instructions = self.config["reviews"]["instructions"].lower()
        # The instructions explicitly mention PII-related identifiers
        self.assertIn("email", instructions)

    def test_instructions_prohibit_aws_credentials(self):
        instructions = self.config["reviews"]["instructions"].lower()
        self.assertIn("aws credential", instructions)

    # ------------------------------------------------------------------
    # reviews.path_filters
    # ------------------------------------------------------------------

    def test_path_filters_is_list(self):
        self.assertIsInstance(self.config["reviews"]["path_filters"], list)

    def test_path_filters_exclude_env_files(self):
        filters = self.config["reviews"]["path_filters"]
        self.assertIn("!**/.env", filters, "Must exclude .env files")

    def test_path_filters_exclude_dotenv_variants(self):
        filters = self.config["reviews"]["path_filters"]
        self.assertIn("!**/.env.*", filters)
        self.assertIn("!**/*.env", filters)
        self.assertIn("!docker/**/*.env", filters)

    def test_path_filters_exclude_secrets_directory(self):
        filters = self.config["reviews"]["path_filters"]
        self.assertIn("!**/secrets/**", filters)

    def test_path_filters_exclude_credentials_files(self):
        filters = self.config["reviews"]["path_filters"]
        self.assertIn("!**/*credentials*", filters)

    def test_path_filters_exclude_secret_files(self):
        filters = self.config["reviews"]["path_filters"]
        self.assertIn("!**/*secret*", filters)

    def test_all_path_filters_are_exclusions(self):
        """Every path filter must be a negation (starts with '!')."""
        for f in self.config["reviews"]["path_filters"]:
            self.assertTrue(
                f.startswith("!"),
                f"path_filter '{f}' should start with '!' (exclusion)",
            )

    def test_path_filters_count(self):
        """Exactly 7 exclusion filters must be present."""
        self.assertEqual(len(self.config["reviews"]["path_filters"]), 7)

    # ------------------------------------------------------------------
    # reviews.path_instructions
    # ------------------------------------------------------------------

    def test_path_instructions_is_list(self):
        self.assertIsInstance(
            self.config["reviews"]["path_instructions"], list
        )

    def test_path_instructions_count(self):
        self.assertEqual(
            len(self.config["reviews"]["path_instructions"]),
            3,
            "Expected exactly 3 path_instructions entries",
        )

    def _get_path_instruction(self, path_glob):
        for entry in self.config["reviews"]["path_instructions"]:
            if entry.get("path") == path_glob:
                return entry
        return None

    def test_path_instructions_settings_entry_exists(self):
        entry = self._get_path_instruction("settings/**")
        self.assertIsNotNone(
            entry, "path_instructions must contain an entry for 'settings/**'"
        )

    def test_path_instructions_settings_entry_has_instructions(self):
        entry = self._get_path_instruction("settings/**")
        self.assertIn("instructions", entry)
        self.assertTrue(entry["instructions"].strip())

    def test_path_instructions_tests_entry_exists(self):
        entry = self._get_path_instruction("tests/**")
        self.assertIsNotNone(
            entry, "path_instructions must contain an entry for 'tests/**'"
        )

    def test_path_instructions_apps_entry_exists(self):
        entry = self._get_path_instruction("apps/**")
        self.assertIsNotNone(
            entry, "path_instructions must contain an entry for 'apps/**'"
        )

    def test_path_instructions_each_entry_has_path_and_instructions(self):
        for entry in self.config["reviews"]["path_instructions"]:
            self.assertIn("path", entry)
            self.assertIn("instructions", entry)
            self.assertTrue(entry["path"].strip())
            self.assertTrue(entry["instructions"].strip())

    # ------------------------------------------------------------------
    # reviews.auto_review
    # ------------------------------------------------------------------

    def test_auto_review_is_dict(self):
        self.assertIsInstance(self.config["reviews"]["auto_review"], dict)

    def test_auto_review_enabled(self):
        self.assertIs(self.config["reviews"]["auto_review"]["enabled"], True)

    def test_auto_review_drafts_enabled(self):
        self.assertIs(self.config["reviews"]["auto_review"]["drafts"], True)

    def test_auto_review_base_branches_is_list(self):
        self.assertIsInstance(
            self.config["reviews"]["auto_review"]["base_branches"], list
        )

    def test_auto_review_base_branches_matches_all(self):
        """The wildcard '.*' must be present so all branches are reviewed."""
        self.assertIn(".*", self.config["reviews"]["auto_review"]["base_branches"])

    def test_auto_review_ignore_usernames_is_list(self):
        self.assertIsInstance(
            self.config["reviews"]["auto_review"]["ignore_usernames"], list
        )

    def test_auto_review_ignores_dependabot(self):
        self.assertIn(
            "dependabot[bot]",
            self.config["reviews"]["auto_review"]["ignore_usernames"],
        )

    def test_auto_review_ignores_renovate(self):
        self.assertIn(
            "renovate[bot]",
            self.config["reviews"]["auto_review"]["ignore_usernames"],
        )

    # ------------------------------------------------------------------
    # reviews.tools – secret-scanning tools must all be enabled
    # ------------------------------------------------------------------

    def test_tools_section_is_dict(self):
        self.assertIsInstance(self.config["reviews"]["tools"], dict)

    def test_gitleaks_enabled(self):
        self.assertIs(
            self.config["reviews"]["tools"]["gitleaks"]["enabled"],
            True,
            "gitleaks must be enabled for secret scanning",
        )

    def test_trufflehog_enabled(self):
        self.assertIs(
            self.config["reviews"]["tools"]["trufflehog"]["enabled"],
            True,
            "trufflehog must be enabled for secret scanning",
        )

    def test_presidio_enabled(self):
        self.assertIs(
            self.config["reviews"]["tools"]["presidio"]["enabled"],
            True,
            "presidio must be enabled for PII detection",
        )

    def test_all_three_scanning_tools_present(self):
        tools = self.config["reviews"]["tools"]
        for tool in ("gitleaks", "trufflehog", "presidio"):
            self.assertIn(
                tool,
                tools,
                f"Tool '{tool}' must be declared in reviews.tools",
            )

    # ------------------------------------------------------------------
    # chat
    # ------------------------------------------------------------------

    def test_chat_section_is_dict(self):
        self.assertIsInstance(self.config["chat"], dict)

    def test_chat_auto_reply_enabled(self):
        self.assertIs(self.config["chat"]["auto_reply"], True)

    # ------------------------------------------------------------------
    # Regression / boundary: no unexpected top-level keys
    # ------------------------------------------------------------------

    def test_no_unexpected_top_level_keys(self):
        allowed = {"language", "reviews", "chat"}
        extra = set(self.config.keys()) - allowed
        self.assertFalse(
            extra,
            f"Unexpected top-level keys in .coderabbit.yaml: {extra}",
        )


# ---------------------------------------------------------------------------
# .presidiocli tests
# ---------------------------------------------------------------------------


class PresidioCLITests(unittest.TestCase):
    """Validate the structure and values of .presidiocli."""

    @classmethod
    def setUpClass(cls):
        cls.config = _load_yaml(PRESIDIOCLI_PATH)

    # ------------------------------------------------------------------
    # File-level sanity
    # ------------------------------------------------------------------

    def test_file_exists(self):
        self.assertTrue(
            os.path.isfile(PRESIDIOCLI_PATH),
            ".presidiocli must exist at the repository root",
        )

    def test_parses_as_valid_yaml(self):
        self.assertIsInstance(self.config, dict)

    def test_top_level_keys_present(self):
        for key in ("language", "threshold", "ignore", "entities"):
            self.assertIn(
                key,
                self.config,
                f"Top-level key '{key}' missing from .presidiocli",
            )

    # ------------------------------------------------------------------
    # language
    # ------------------------------------------------------------------

    def test_language_is_english(self):
        self.assertEqual(self.config["language"], "en")

    # ------------------------------------------------------------------
    # threshold
    # ------------------------------------------------------------------

    def test_threshold_is_numeric(self):
        self.assertIsInstance(self.config["threshold"], (int, float))

    def test_threshold_value(self):
        """Threshold must be 0.35 as configured."""
        self.assertAlmostEqual(self.config["threshold"], 0.35, places=5)

    def test_threshold_within_valid_range(self):
        """Presidio thresholds must be in [0.0, 1.0]."""
        self.assertGreaterEqual(self.config["threshold"], 0.0)
        self.assertLessEqual(self.config["threshold"], 1.0)

    def test_threshold_above_zero(self):
        """A zero threshold would flag everything; confirm it is positive."""
        self.assertGreater(self.config["threshold"], 0.0)

    # ------------------------------------------------------------------
    # ignore
    # ------------------------------------------------------------------

    def test_ignore_contains_git_directory(self):
        """The .git directory must be ignored to avoid scanning VCS internals."""
        ignore_text = self.config.get("ignore", "")
        self.assertIn(".git", ignore_text)

    def test_ignore_is_string(self):
        self.assertIsInstance(self.config["ignore"], str)

    # ------------------------------------------------------------------
    # entities
    # ------------------------------------------------------------------

    EXPECTED_ENTITIES = {
        "CREDIT_CARD",
        "CRYPTO",
        "EMAIL_ADDRESS",
        "IBAN_CODE",
        "PHONE_NUMBER",
        "US_BANK_NUMBER",
        "US_ITIN",
        "US_SSN",
    }

    def test_entities_is_list(self):
        self.assertIsInstance(self.config["entities"], list)

    def test_entities_count(self):
        self.assertEqual(
            len(self.config["entities"]),
            8,
            "Expected exactly 8 PII entities in .presidiocli",
        )

    def test_credit_card_entity_present(self):
        self.assertIn("CREDIT_CARD", self.config["entities"])

    def test_crypto_entity_present(self):
        self.assertIn("CRYPTO", self.config["entities"])

    def test_email_address_entity_present(self):
        self.assertIn("EMAIL_ADDRESS", self.config["entities"])

    def test_iban_code_entity_present(self):
        self.assertIn("IBAN_CODE", self.config["entities"])

    def test_phone_number_entity_present(self):
        self.assertIn("PHONE_NUMBER", self.config["entities"])

    def test_us_bank_number_entity_present(self):
        self.assertIn("US_BANK_NUMBER", self.config["entities"])

    def test_us_itin_entity_present(self):
        self.assertIn("US_ITIN", self.config["entities"])

    def test_us_ssn_entity_present(self):
        self.assertIn("US_SSN", self.config["entities"])

    def test_all_expected_entities_present(self):
        actual = set(self.config["entities"])
        self.assertEqual(actual, self.EXPECTED_ENTITIES)

    def test_no_duplicate_entities(self):
        entities = self.config["entities"]
        self.assertEqual(
            len(entities),
            len(set(entities)),
            "Duplicate entity types found in .presidiocli",
        )

    def test_all_entities_are_strings(self):
        for entity in self.config["entities"]:
            self.assertIsInstance(
                entity, str, f"Entity '{entity}' must be a string"
            )

    def test_all_entities_are_uppercase(self):
        """Presidio entity names are conventionally upper-case."""
        for entity in self.config["entities"]:
            self.assertEqual(
                entity,
                entity.upper(),
                f"Entity '{entity}' should be uppercase",
            )

    # ------------------------------------------------------------------
    # Regression: threshold boundary – ensure it is not too permissive
    # ------------------------------------------------------------------

    def test_threshold_not_below_minimum_recommended(self):
        """
        A threshold below 0.3 is generally considered too permissive for
        production PII scanning. Ensures the configured value stays >= 0.3.
        """
        self.assertGreaterEqual(
            self.config["threshold"],
            0.3,
            "Threshold is unexpectedly low; may produce too many false positives",
        )


if __name__ == "__main__":
    unittest.main()
