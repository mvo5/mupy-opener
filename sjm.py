#!/usr/bin/python3

import binascii
import json

from uhmac import HMAC

try:
    from typing import Any, Callable, Dict
except ImportError:
    pass


def b64encode_to_str(b):
    return binascii.b2a_base64(b).decode("utf-8").strip()


def b64decode_from_str(s):
    return binascii.a2b_base64(s)


def b64encode_json(obj):
    return b64encode_to_str(json.dumps(obj).encode("utf-8"))


class InvalidFormatError(Exception):
    pass


class InvalidSignatureError(Exception):
    pass


class InvalidNonceError(Exception):
    pass


class SignedJsonMessage:
    """Signed Json Message is an encoded signed json message to communicate
    between two parties that share a (pre-shared) secret key.

    The communication is secured using a HMAC to ensure authentication and
    a nonce to protect against reply attacks.

    Each message consists of a header that has the algorithm, nonce
    and optionally key-id as base64 encoded json. Then a separator
    ".".  Then the payload as base64 encoded json. Then a separator
    ".". And last the signature of the header+payload.

    Note that *no* encryption is performed (would be trivial to add).

    The schema is very similar to JWT, expect that it adds a mandatory
    nonce and uses plain base64 (because micropython has no
    urlsafe_b64encode).
    """

    def __init__(self, key, nonce):
        # type: (bytes, str, Callable[..., Any]) -> None
        self._header = {"ver": "1", "alg": "HS256", "nonce": nonce}
        self._payload = {}  # type: Dict[Any, Any]
        self._key = key

    def set_payload(self, payload):
        self._payload = payload

    @property
    def payload(self):
        return self._payload

    @property
    def nonce(self):
        return self._header["nonce"]

    def __str__(self):
        # type: () -> str
        hp = "%s.%s" % (b64encode_json(self._header), b64encode_json(self._payload))
        sig = HMAC(self._key, hp.encode("utf-8"), "sha256")
        return "%s.%s" % (hp, b64encode_to_str(sig.digest()))

    @staticmethod
    def from_string(s, key, expected_nonce=None):
        # type: (str, bytes, str,  Callable[..., Any]) -> SignedJsonMessage
        try:
            encoded_header_payload, encoded_signature = s.rsplit(".", 1)
        except ValueError:
            raise InvalidFormatError("invalid data format '%s'" % s)
        recv_sig = b64decode_from_str(encoded_signature)
        calculated_sig = HMAC(
            key, encoded_header_payload.encode("utf-8"), "sha256"
        ).digest()
        # XXX: micropython has no "compare_digest"
        if calculated_sig != recv_sig:
            raise InvalidSignatureError()
        # XXX: compare protocol version and error on mismatch
        # sig ok, continue
        encoded_header, encoded_payload = encoded_header_payload.split(".")
        header = json.loads(b64decode_from_str(encoded_header))
        payload = json.loads(b64decode_from_str(encoded_payload))
        if expected_nonce:
            if header.get("nonce") != expected_nonce:
                raise InvalidNonceError()
        nonce = header.get("nonce")
        sjm = SignedJsonMessage(key, nonce)
        sjm.set_payload(payload)
        return sjm


def test():
    import time

    if hasattr(time, "tick_ms"):
        now = time.ticks_ms()
    msg = SignedJsonMessage("key".encode("utf-8"), "nonce")
    print(msg)
    sjm1 = SignedJsonMessage.from_string(str(msg), "key".encode("utf-8"), "nonce")
    print(sjm1)
    if hasattr(time, "tick_ms"):
        print("total time: {}".format(time.ticks_ms() - now))


if __name__ == "__main__":
    test()
