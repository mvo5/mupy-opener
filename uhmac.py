try:
    from uhashlib import sha1, sha256
except ImportError:
    from hashlib import sha1, sha256


# From https://en.wikipedia.org/wiki/Hash-based_message_authentication_code
def HMAC(key, msg, digestmod):
    block_size = 64
    fn = None
    if digestmod == "sha256":
        fn = sha256
    elif digestmod == "sha1":
        fn = sha1
    else:
        raise ValueError("cannot use digest mode {}".format(digestmod))

    if len(key) > block_size:
        key = fn(key).digest()
    key_block = key + (b"\0" * (block_size - len(key)))
    inner = bytes((x ^ 0x36) for x in key_block)
    outer = bytes((x ^ 0x5C) for x in key_block)
    inner_message = inner + msg
    outer_message = outer + fn(inner_message).digest()
    return fn(outer_message)
