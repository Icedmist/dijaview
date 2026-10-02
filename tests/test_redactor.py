import unittest
from dijaview.core.redactor import redact_secrets


class TestRedactor(unittest.TestCase):
    def test_redact_bearer_token(self):
        raw = "curl -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9' https://api.com"
        sanitized = redact_secrets(raw)
        self.assertIn("[REDACTED_TOKEN]", sanitized)
        self.assertNotIn("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9", sanitized)

    def test_redact_github_token(self):
        raw = "git clone https://ghp_1234567890abcdefghijklmnopqrstuvwxyzAB@github.com/repo"
        sanitized = redact_secrets(raw)
        self.assertIn("[REDACTED_GITHUB_KEY]", sanitized)
        self.assertNotIn("ghp_", sanitized)

    def test_redact_database_uri(self):
        raw = "DATABASE_URL=postgres://app_user:super_secret_password_123@db.internal:5432/production"
        sanitized = redact_secrets(raw)
        self.assertIn("[REDACTED_PASSWORD]", sanitized)
        self.assertNotIn("super_secret_password_123", sanitized)

    def test_redact_private_key(self):
        raw = """
        -----BEGIN RSA PRIVATE KEY-----
        MIIEowIBAAKCAQEA0Y123456789abcdefghijklmnopqrstuvwxyz
        -----END RSA PRIVATE KEY-----
        """
        sanitized = redact_secrets(raw)
        self.assertIn("[REDACTED_PRIVATE_KEY]", sanitized)
        self.assertNotIn("MIIEowIBAAKCAQEA0Y123456789", sanitized)


if __name__ == "__main__":
    unittest.main()
