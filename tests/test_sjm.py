import unittest

import sjm


class TestSignedJsonMessage(unittest.TestCase):
    def setUp(self):
        self.bytes_key = "key".encode("utf-8")
        self.nonce = "nonce"
        self.sjmsg = sjm.SignedJsonMessage(self.bytes_key, self.nonce)
        self.sjmsg.set_payload({"foo": "bar"})

    def test_sjm_create(self):
        self.assertEqual(self.sjmsg._header["nonce"], self.nonce)
        self.assertEqual(self.sjmsg._payload, {"foo": "bar"})
        # no newline at the end of the str
        self.assertNotEqual(str(self.sjmsg)[-1], "\n")

    def test_sjm_from_string(self):
        sjmsg2 = sjm.SignedJsonMessage.from_string(
            str(self.sjmsg), self.bytes_key, self.nonce
        )
        self.assertEqual(self.sjmsg._header, sjmsg2._header)
        self.assertEqual(self.sjmsg._payload, sjmsg2._payload)
        self.assertEqual(str(self.sjmsg), str(sjmsg2))

    def test_sjm_from_string2(self):
        msg = sjm.SignedJsonMessage.from_string(
            "eyJhbGciOiJIUzI1NiIsIm5vbmNlIjoibm9uY2UiLCJ2ZXIiOiIxIn0="
            ".eyJmb28iOiJiYXIifQ==.5sO1KIJIGn/ZAAwvWui9/gIHrfntLYFVnz"
            "57aMBOCCY=",
            b"key",
            "nonce",
        )
        print(msg)

    def test_create_sjm(self):
        msg = sjm.SignedJsonMessage(b"key", "nonce")
        msg.set_payload({"foo": "bar"})
        self.assertEqual(
            str(msg),
            "eyJ2ZXIiOiAiMSIsICJhbGciOiAiSFMyNTYiLCAibm9uY2UiOiAi"
            "bm9uY2UifQ==.eyJmb28iOiAiYmFyIn0=.7WdCzTIR0FP9ssODM8"
            "xxRiwW3BkTvTw0SiIlTW/oUdk=",
        )

    def test_sjm_from_string_wrong_format_empty(self):
        with self.assertRaises(sjm.InvalidFormatError):
            sjm.SignedJsonMessage.from_string("", b"other-key", self.nonce)

    def test_sjm_from_string_wrong_sig(self):
        with self.assertRaises(sjm.InvalidSignatureError):
            sjm.SignedJsonMessage.from_string(str(self.sjmsg), b"other-key", self.nonce)

    def test_sjm_from_string_wrong_nonce(self):
        with self.assertRaises(sjm.InvalidNonceError):
            sjm.SignedJsonMessage.from_string(
                str(self.sjmsg), self.bytes_key, "other-nonce"
            )

    def test_sjm_from_string_nonce_is_optional(self):
        # nonce is not checked
        sjmsg3 = sjm.SignedJsonMessage.from_string(
            str(self.sjmsg), self.bytes_key, expected_nonce=None
        )
        # but the nonce from the string is set
        self.assertEqual(self.sjmsg._header["nonce"], self.nonce)
        # and the sjmsg3 is the same
        self.assertEqual(str(self.sjmsg), str(sjmsg3))
