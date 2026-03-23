"""Tests for utility helpers."""

from __future__ import annotations

import os
import tempfile
import unittest

from chirpier.utils import is_valid_api_key, resolve_api_key


class TestUtils(unittest.TestCase):
    def test_is_valid_api_key(self):
        self.assertTrue(is_valid_api_key("chp_valid"))
        self.assertFalse(is_valid_api_key("invalid"))
        self.assertFalse(is_valid_api_key("chp_"))

    def test_resolve_api_key_precedence(self):
        old_env = os.getenv("CHIRPIER_API_KEY")
        try:
            os.environ["CHIRPIER_API_KEY"] = "chp_from_env"
            self.assertEqual(resolve_api_key("chp_from_options"), "chp_from_options")
            self.assertEqual(resolve_api_key(None), "chp_from_env")
        finally:
            if old_env is None:
                os.environ.pop("CHIRPIER_API_KEY", None)
            else:
                os.environ["CHIRPIER_API_KEY"] = old_env

    def test_resolve_api_key_from_dotenv(self):
        old_env = os.getenv("CHIRPIER_API_KEY")
        cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as tmpdir:
            try:
                os.environ.pop("CHIRPIER_API_KEY", None)
                os.chdir(tmpdir)
                with open(".env", "w", encoding="utf-8") as dotenv_file:
                    dotenv_file.write("CHIRPIER_API_KEY=chp_from_dotenv\n")

                self.assertEqual(resolve_api_key(None), "chp_from_dotenv")
            finally:
                os.chdir(cwd)
                if old_env is None:
                    os.environ.pop("CHIRPIER_API_KEY", None)
                else:
                    os.environ["CHIRPIER_API_KEY"] = old_env


if __name__ == "__main__":
    unittest.main()
