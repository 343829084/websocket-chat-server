from Crypto.Cipher import AES
from Crypto import Random

"""Encrypts/decrypts data for the CryptoJS JavaScript module
use mode: CryptoJS.mode.CFB
    padding: CryptoJS.pad.Pkcs7
    a 16 byte key and a 16 byte iv
"""


def unpad_bytes(bytes):
    '''Remove the PKCS#7 padding from a bytearray'''
    in_len = len(bytes)
    pad_size = bytes[-1]
    if pad_size > 16:
        raise ValueError('Input is not padded or padding is corrupt')
    return bytes[:in_len - pad_size]


def pad_bytes(bytes):
    '''Pad an input string according to PKCS#7'''
    in_len = len(bytes)
    pad_size = 16 - (in_len % 16)
    return bytes.ljust(in_len + pad_size, pad_size.to_bytes(1, 'big'))


def decrypt(bytes, key, iv):
    aes = AES.new(key, AES.MODE_CFB, iv, segment_size=128)
    decrypted = aes.decrypt(bytes)
    return unpad_bytes(decrypted)


def encrypt(bytes, key=None, iv=None):
    if key is None and iv is None:
        key = Random.get_random_bytes(16)
        iv = Random.get_random_bytes(16)
    aes = AES.new(key, AES.MODE_CFB, iv, segment_size=128)
    encrypted = aes.encrypt(pad_bytes(bytes))
    if key is None and iv is None:
        return key, iv, encrypted
    else:
        return encrypted


def generate_key_and_iv(one=False):
    keyiv = Random.get_random_bytes(32)

    if one:
        return keyiv.hex()
    else:
        return keyiv[:16], keyiv[16:]


if __name__ == '__main__':
    key, iv = generate_key_and_iv()
    string = b'hello there'
    encrypted = encrypt(string, key, iv)
    decrypted = decrypt(encrypted, key, iv)
    print('String: ', string)
    print('Key: ', key)
    print('iv: ', iv)
    print('len(encrypted)', len(encrypted))
    print('Encrypted: ', encrypted)
    print('Decrypted: ', decrypted)
