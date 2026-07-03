from pathlib import Path

from cryptography.fernet import Fernet

from src.config import settings


def _ensure_data_dir() -> Path:
    path = settings.data_dir
    path.mkdir(parents=True, exist_ok=True)
    return path


def _load_or_create_key(key_path: Path, env_key: str) -> bytes:
    if env_key:
        return env_key.encode() if isinstance(env_key, str) else env_key

    if key_path.exists():
        return key_path.read_bytes()

    key = Fernet.generate_key()
    key_path.write_bytes(key)
    key_path.chmod(0o600)
    return key


def get_fernet() -> Fernet:
    data_dir = _ensure_data_dir()
    key = _load_or_create_key(
        data_dir / "fernet.key",
        settings.FERNET_KEY,
    )
    return Fernet(key)


def encrypt(plain_text: str) -> bytes:
    f = get_fernet()
    return f.encrypt(plain_text.encode())


def decrypt(token: bytes) -> str:
    f = get_fernet()
    return f.decrypt(token).decode()


def get_secret_key() -> str:
    data_dir = _ensure_data_dir()
    key_path = data_dir / "secret.key"
    env_key = settings.SECRET_KEY

    if env_key:
        return env_key

    if key_path.exists():
        return key_path.read_text().strip()

    key = Fernet.generate_key().decode()
    key_path.write_text(key)
    key_path.chmod(0o600)
    return key


def rotate_secret_key() -> str:
    data_dir = _ensure_data_dir()
    key_path = data_dir / "secret.key"
    new_key = Fernet.generate_key().decode()
    key_path.write_text(new_key)
    key_path.chmod(0o600)
    return new_key
