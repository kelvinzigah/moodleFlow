from cryptography.fernet import Fernet
from school_assistant.config import Settings


def test_settings_load_portable_runtime_configuration_from_environment(
    monkeypatch,
) -> None:
    key = Fernet.generate_key().decode()
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://app:secret@postgres/app")
    monkeypatch.setenv("CREDENTIAL_KEY", key)
    monkeypatch.setenv("CORS_ORIGINS", '["http://localhost:5173"]')
    monkeypatch.setenv("TELEGRAM_MODE", "long_polling")

    settings = Settings(_env_file=None)

    assert str(settings.database_url) == "postgresql+asyncpg://app:secret@postgres/app"
    assert settings.credential_key.get_secret_value() == key
    assert settings.cors_origins == ["http://localhost:5173"]
    assert settings.telegram_mode == "long_polling"
