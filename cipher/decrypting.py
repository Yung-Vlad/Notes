from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

import base64
from cipher.generate import KEYS_PATH


# Decrypting aes_key by private key
def decrypt_aes_key(private_pem: bytes, encrypted_aes_key: bytes) -> bytes:
    private_key = serialization.load_pem_private_key(private_pem, password=None)

    # Decrypted data
    decrypted_data = private_key.decrypt(
        encrypted_aes_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )

    return decrypted_data


def symmetric_decrypt_data(key: bytes, data: str) -> str:
    data = base64.b64decode(data)
    iv = data[:12]  # First 12 bits with iv
    tag = data[12:28]  # From 12 to 28 bits with tag
    text = data[28:]  # Remaining bits with decrypted text

    decryptor = Cipher(
        algorithms.AES(key),
        modes.GCM(iv, tag),
        backend=default_backend()
    ).decryptor()

    return (decryptor.update(text) + decryptor.finalize()).decode()


# Decrypt note
def decrypt_note(note: dict, username: str, aes_key: bytes) -> dict:
    private_pem = get_private_key(username)
    secret_key = decrypt_aes_key(private_pem, aes_key)

    note["header"] = symmetric_decrypt_data(secret_key, note["header"])
    note["content"] = symmetric_decrypt_data(secret_key, note["content"])
    note["tags"] = symmetric_decrypt_data(secret_key, note["tags"])

    return note


# Read private key from file
def get_private_key(username: str) -> bytes:
    with open(f"{KEYS_PATH}/{username}_key.pem", "rb") as file:
        return file.read()
