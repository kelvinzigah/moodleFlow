from cryptography.fernet import Fernet
from school_assistant.crypto import CredentialCipher


def test_credentials_are_encrypted_at_rest_and_can_be_recovered() -> None:
    cipher = CredentialCipher(Fernet.generate_key().decode())

    encrypted = cipher.encrypt("moodle-secret-token")

    assert "moodle-secret-token" not in encrypted
    assert cipher.decrypt(encrypted) == "moodle-secret-token"
