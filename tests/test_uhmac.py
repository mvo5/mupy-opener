import unittest

import uhmac


class TestHMAC(unittest.TestCase):

    # see https://datatracker.ietf.org/doc/html/rfc4231
    def test_hmac_sha256(self):
        def sha256test(key, data, expected_hmac):
            hmac = uhmac.HMAC(key, data, "sha256")
            self.assertEqual(hmac.hexdigest(), expected_hmac)

        # Test Case 1
        key = b"\x0b" * 20
        data = b"Hi There"
        expected_hmac = (
            "b0344c61d8db38535ca8afceaf0bf12b881dc200c9833da726e9376c2e32cff7"
        )
        sha256test(key, data, expected_hmac)
        # Test Case 2
        key = b"Jefe"
        data = b"what do ya want for nothing?"
        expected_hmac = (
            "5bdcc146bf60754e6a042426089575c75a003f089d2739839dec58b964ec3843"
        )
        sha256test(key, data, expected_hmac)
        # Test Case 3
        key = b"\xaa" * 20
        data = b"\xdd" * 50
        expected_hmac = (
            "773ea91e36800e46854db8ebd09181a72959098b3ef8c122d9635514ced565fe"
        )
        sha256test(key, data, expected_hmac)
        # Test Case 4
        key = (
            b"\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c"
            b"\x0d\x0e\x0f\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19"
        )
        data = b"\xcd" * 50
        expected_hmac = (
            "82558a389a443c0ea4cc819899f2083a85f0faa3e578f8077a2e3ff46729665b"
        )
        sha256test(key, data, expected_hmac)
        # Test Case 6
        key = b"\xaa" * 131
        data = b"Test Using Larger Than Block-Size Key - Hash Key First"
        expected_hmac = (
            "60e431591ee0b67f0d8a26aacbf5b77f8e0bc6213728c5140546040f0ee37f54"
        )
        sha256test(key, data, expected_hmac)
        # Test Case 7
        key = b"\xaa" * 131
        data = (
            b"This is a test using a larger than block-size key and a larger "
            b"than block-size data. The key needs to be hashed before being "
            b"used by the HMAC algorithm."
        )
        expected_hmac = (
            "9b09ffa71b942fcb27635fbcd5b0e944bfdc63644f0713938a7f51535c3a35e2"
        )
        sha256test(key, data, expected_hmac)

    def test_sha1(self):
        def sha1test(key, data, expected_hmac):
            hmac = uhmac.HMAC(key, data, "sha1")
            self.assertEqual(hmac.hexdigest(), expected_hmac)

        sha1test(b"\x0b" * 20, b"Hi There", "b617318655057264e28bc0b6fb378c8ef146be00")
        sha1test(
            b"Jefe",
            b"what do ya want for nothing?",
            "effcdf6ae5eb2fa2d27416d5f184df9c259a7c79",
        )

        sha1test(b"\xAA" * 20, b"\xDD" * 50, "125d7342b9ac11cd91a39af48aa17b4f63f175d3")
        sha1test(
            bytes(range(1, 26)),
            b"\xCD" * 50,
            "4c9007f4026250c6bc8414f9bf50c86c2d7235da",
        )
        sha1test(
            b"\x0C" * 20,
            b"Test With Truncation",
            "4c1a03424b55e07fe7f27be1d58bb9324a9a5a04",
        )
        sha1test(
            b"\xAA" * 80,
            b"Test Using Larger Than Block-Size Key - Hash Key First",
            "aa4ae5e15272d00e95705637ce8a3b55ed402112",
        )
        sha1test(
            b"\xAA" * 80,
            (
                b"Test Using Larger Than Block-Size Key "
                b"and Larger Than One Block-Size Data"
            ),
            "e8e99d0f45237d786d6bbaa7965c7808bbff1a91",
        )
