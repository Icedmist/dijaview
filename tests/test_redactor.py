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

    def test_redact_paystack_and_stripe_keys(self):
        # Paystack secret key
        dummy_sk_prefix = "sk_" + "live_"
        raw_paystack = f"paystack_secret = '{dummy_sk_prefix}9817850525abcdef9817850525abcdef1234'"
        sanitized_paystack = redact_secrets(raw_paystack)
        self.assertIn("[REDACTED_API_KEY]", sanitized_paystack)
        self.assertNotIn("9817850525", sanitized_paystack)

        # Stripe secret key
        raw_stripe = f"stripe_key = '{dummy_sk_prefix}51Abcdef1234567890abcdef1234567890'"
        sanitized_stripe = redact_secrets(raw_stripe)
        self.assertIn("[REDACTED_API_KEY]", sanitized_stripe)
        self.assertNotIn("51Abcdef", sanitized_stripe)

        # Public key
        dummy_pk_prefix = "pk_" + "test_"
        raw_pk = f"{dummy_pk_prefix}1234567890abcdef1234567890abcdef1234"
        self.assertIn("[REDACTED_API_KEY]", redact_secrets(raw_pk))

    def test_redact_mysql_password(self):
        # Attached -p
        raw1 = "mysql -u root -pSuperSecret123 mydb"
        sanitized1 = redact_secrets(raw1)
        self.assertIn("[REDACTED_PASSWORD]", sanitized1)
        self.assertNotIn("SuperSecret123", sanitized1)

        # Quoted -p
        raw2 = "mysql -u root -p'Super Secret 123' mydb"
        sanitized2 = redact_secrets(raw2)
        self.assertIn("[REDACTED_PASSWORD]", sanitized2)
        self.assertNotIn("Super Secret 123", sanitized2)

        # mysqldump
        raw3 = "mysqldump -u admin -pMyBackupPass production > backup.sql"
        sanitized3 = redact_secrets(raw3)
        self.assertIn("[REDACTED_PASSWORD]", sanitized3)
        self.assertNotIn("MyBackupPass", sanitized3)

    def test_redact_curl_user_pass(self):
        # Unquoted curl -u
        raw1 = "curl -u admin:my_api_password_456 https://example.com/api"
        sanitized1 = redact_secrets(raw1)
        self.assertIn("admin:[REDACTED_PASSWORD]", sanitized1)
        self.assertNotIn("my_api_password_456", sanitized1)

        # Quoted curl -u
        raw2 = 'curl -u "admin:secret pass 123" https://example.com/api'
        sanitized2 = redact_secrets(raw2)
        self.assertIn('admin:[REDACTED_PASSWORD]', sanitized2)
        self.assertNotIn("secret pass 123", sanitized2)

        # curl --user
        raw3 = "curl --user apiuser:sec123 https://example.com/api"
        sanitized3 = redact_secrets(raw3)
        self.assertIn("apiuser:[REDACTED_PASSWORD]", sanitized3)
        self.assertNotIn("sec123", sanitized3)

    def test_redact_sshpass(self):
        raw = "sshpass -p 'MySshPassword' ssh snow@192.168.1.1"
        sanitized = redact_secrets(raw)
        self.assertIn("[REDACTED_PASSWORD]", sanitized)
        self.assertNotIn("MySshPassword", sanitized)

    def test_redact_jwt(self):
        raw = "Token received: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIn0.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c in session"
        sanitized = redact_secrets(raw)
        self.assertIn("[REDACTED_JWT]", sanitized)
        self.assertNotIn("SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c", sanitized)

    def test_redact_aws_and_export(self):
        dummy_aws_secret = "wJalrXUtn" + "FEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
        raw_aws = f"AWS_SECRET_ACCESS_KEY={dummy_aws_secret}"
        sanitized_aws = redact_secrets(raw_aws)
        self.assertIn("[REDACTED_AWS_SECRET]", sanitized_aws)
        self.assertNotIn("wJalrXUtn", sanitized_aws)

        raw_export = "export API_TOKEN=my_production_token_xyz123"
        sanitized_export = redact_secrets(raw_export)
        self.assertIn("[REDACTED_SECRET]", sanitized_export)
        self.assertNotIn("my_production_token_xyz123", sanitized_export)


if __name__ == "__main__":
    unittest.main()
