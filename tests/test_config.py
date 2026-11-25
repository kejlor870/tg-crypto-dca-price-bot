import unittest
from unittest.mock import patch

from app.config import load_config, PROJECT_ROOT


class TestConfig(unittest.TestCase):

    @patch.dict(
        "os.environ",
        {
            "BOT_TOKEN": "test-token",
            "ALLOWED_USER_ID": "123456789",
            "DATABASE_PATH": "data/crypto_tracker.db",
        },
        clear=True,
    )
    def test_load_config_with_valid_environment(self):
        config = load_config()

        self.assertEqual(config.telegram_bot_token, "test-token")
        self.assertEqual(config.telegram_user_id, 123456789)
        self.assertEqual(config.database_path, PROJECT_ROOT / "data" / "crypto_tracker.db")

    @patch.dict(
        "os.environ",
        {
            "BOT_TOKEN": "test-token",
            "ALLOWED_USER_ID": "abcd",
            "DATABASE_PATH": "data/crypto_tracker.db",
        }
    )
    def test_load_config_with_invalid_user_id_raises_error(self):
        with self.assertRaisesRegex(ValueError, "must be an integer"):
            load_config()

    @patch.dict(
        "os.environ",
        {
            "BOT_TOKEN": "test-token",
            "ALLOWED_USER_ID": "123456789",
            "DATABASE_PATH": "data/crypto_tracker.db",
        },
        clear=True,
    )
    def test_load_config_resolves_relative_database_path(self):
        config = load_config()

        self.assertTrue(config.database_path.is_absolute())
        self.assertEqual(config.database_path, PROJECT_ROOT / "data" / "crypto_tracker.db")


if __name__ == "__main__":
    unittest.main()
