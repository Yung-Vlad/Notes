from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

import os
from dotenv import load_dotenv


load_dotenv()
KEYS_PATH = os.getenv("KEYS_PATH")


def generate_asymmetric_keys(username: str) -> str:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()

    create_dir_if_not_exists()

    # Create private key and save it on server
    with open(f"{KEYS_PATH}/{username}_key.pem", "wb") as file:
        file.write(
            private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption()
            )
        )

    # Create public key then save it on db
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

    return public_pem.decode()


def generate_aes_key() -> bytes:
    aes_key_length = 32  # Length of key
    key = os.urandom(aes_key_length)

    return key


def create_dir_if_not_exists() -> None:
    if not os.path.exists(KEYS_PATH):
        os.mkdir(KEYS_PATH)
