import base64
import json
import os
from os.path import abspath

import keyring
from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt

KEYRING_SERVICE = 'com.3stack.nv'


def keyring_store(nv_dir, password):
    keyring.set_password(KEYRING_SERVICE, abspath(nv_dir), password)
    return


def keyring_retrieve(nv_dir):
    try:
        return keyring.get_password(KEYRING_SERVICE, abspath(nv_dir))
    except:
        pass


class DisabledCrypto(object):

    def get_memo(self):
        return None

    def json_load(self, fp):
        return json.load(fp)

    def json_dump(self, fp, obj):
        return json.dump(obj, fp, indent=2)


class Crypto(object):

    def __init__(self, salt, key):
        self._salt = salt
        self._engine = Fernet(key)

    @classmethod
    def from_password(cls, password):
        salt = cls.generate_salt()
        key = cls.derive_key(salt, password)
        return cls(salt, key)

    @classmethod
    def from_memo(cls, memo, password):
        if not isinstance(memo, dict):
            raise ValueError('No encryption metadata found')
        version = memo.get('version')
        if version != '1':
            raise ValueError('Unsupported version: {!r}'.format(version))

        key = cls.derive_key(memo['salt'], password)
        return cls(memo['salt'], key)

    def get_memo(self):
        return {
            'version': '1',
            'salt': self._salt
        }

    def json_load(self, fp):
        ciphertext = fp.read()
        plaintext = self._engine.decrypt(ciphertext)
        return json.loads(plaintext)

    def json_dump(self, fp, obj):
        plaintext = json.dumps(obj, indent=2)
        ciphertext = self._engine.encrypt(plaintext)
        fp.write(ciphertext)

    @staticmethod
    def derive_key(salt, password, key_length=32):
        if isinstance(salt, str):
            salt = salt.encode('utf-8')
        if isinstance(password, str):
            password = password.encode('utf-8')
        kdf = Scrypt(
            salt=base64.urlsafe_b64decode(salt),
            length=key_length,
            n=2**14,
            r=8,
            p=1,
            backend=default_backend(),
        )
        key = kdf.derive(password)
        return base64.urlsafe_b64encode(key)

    @staticmethod
    def generate_salt(n=16):
        salt = os.urandom(n)
        return base64.urlsafe_b64encode(salt)
