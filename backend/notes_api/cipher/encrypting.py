from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

import base64, os
from schemas.notes import NoteInternalSchema, NoteUpdateInternalSchema


# Encrypting aes_key by public key
def encrypt_aes_key(public_pem: bytes, key: bytes) -> bytes:
    public_key = serialization.load_pem_public_key(public_pem)  # Load pub_key

    # Encrypted data
    encrypted_key = public_key.encrypt(
        key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )

    return encrypted_key


def symmetric_encrypt_data(key: bytes, data: str) -> str:
    iv = os.urandom(12)  # Length of initialize vector

    encryptor = Cipher(
        algorithms.AES(key),
        modes.GCM(iv),
        backend=default_backend()
    ).encryptor()

    data = encryptor.update(data.encode()) + encryptor.finalize()

    return base64.b64encode(iv + encryptor.tag + data).decode()


# Symmetric encrypting note
def symmetric_encrypt_note(key: bytes, note: NoteInternalSchema | NoteUpdateInternalSchema) -> NoteInternalSchema | NoteUpdateInternalSchema:

    note.header = symmetric_encrypt_data(key, note.header)
    note.text = symmetric_encrypt_data(key, note.text)
    note.tags = symmetric_encrypt_data(key, note.tags)

    return note
