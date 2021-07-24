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
            str(self.sjmsg), self.bytes_key, self.nonce)
        self.assertEqual(self.sjmsg._header, sjmsg2._header)
        self.assertEqual(self.sjmsg._payload, sjmsg2._payload)
        self.assertEqual(str(self.sjmsg), str(sjmsg2))

    def test_sjm_from_string_wrong_sig(self):
        with self.assertRaises(sjm.InvalidSignatureError):
            sjm.SignedJsonMessage.from_string(
                str(self.sjmsg), b"other-key", self.nonce)

    def test_sjm_from_string_wrong_nonce(self):
        with self.assertRaises(sjm.InvalidNonceError):
            sjm.SignedJsonMessage.from_string(
                str(self.sjmsg), self.bytes_key, "other-nonce")

    def test_sjm_from_string_nonce_is_optional(self):
        # nonce is not checked
        sjmsg3 = sjm.SignedJsonMessage.from_string(
            str(self.sjmsg), self.bytes_key, expected_nonce=None)
        # but the nonce from the string is set
        self.assertEqual(self.sjmsg._header["nonce"], self.nonce)
        # and the sjmsg3 is the same
        self.assertEqual(str(self.sjmsg), str(sjmsg3))
