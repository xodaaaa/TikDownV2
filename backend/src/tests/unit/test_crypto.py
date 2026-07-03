import tempfile
from pathlib import Path

import pytest
from cryptography.fernet import Fernet

from src.core.crypto import decrypt, encrypt, get_fernet


class TestCrypto:
    def test_encrypt_decrypt_roundtrip(self):
        original = "sessionid=abc123; tt_csrf_token=xyz"
        encrypted = encrypt(original)
        assert encrypted != original.encode()
        decrypted = decrypt(encrypted)
        assert decrypted == original

    def test_encrypt_produces_different_tokens(self):
        plain = "test_value"
        t1 = encrypt(plain)
        t2 = encrypt(plain)
        assert t1 != t2

    def test_get_fernet_returns_fernet_instance(self):
        f = get_fernet()
        assert isinstance(f, Fernet)

    def test_get_fernet_hierarchy(self):
        with tempfile.TemporaryDirectory() as tmp:
            import src.config as cfg

            old_data_dir = cfg.settings.data_dir
            cfg.settings.DATABASE_PATH = str(Path(tmp) / "test.db")

            old_fernet_key = cfg.settings.FERNET_KEY
            cfg.settings.FERNET_KEY = ""

            try:
                f1 = get_fernet()
                assert isinstance(f1, Fernet)
                key_path = cfg.settings.data_dir / "fernet.key"
                assert key_path.exists()

                f2 = get_fernet()
                assert f2._encryption_key == f1._encryption_key
            finally:
                cfg.settings.DATABASE_PATH = str(
                    Path("/app/data/tikdown.db")
                )
                cfg.settings.FERNET_KEY = ""
                cfg.settings._data_dir = None

    def test_encrypt_decrypt_empty_string(self):
        original = ""
        encrypted = encrypt(original)
        decrypted = decrypt(encrypted)
        assert decrypted == original

    def test_decrypt_invalid_token_raises(self):
        with pytest.raises(Exception):
            decrypt(b"invalid_token_data_here")
