import multiprocessing
import os
import socket
import time

# from unittest.mock import patch, MagicMock

from tests.test_base import BaseTest

# the actual code
import main
from sjm import SignedJsonMessage


def connect_or_retry(ss, addr, n_tries=10):
    # wait for the socket to get ready
    for i in range(n_tries):
        try:
            ss.connect(addr)
            return
        except Exception:
            pass
        time.sleep(0.1)
    else:
        raise Exception("cannot connect to {}".format(main.PORT))


class TestMain(BaseTest):

    def test_main_network_integration(self):
        # XXX: restore value
        main.OPENER_WAIT = 0.0001
        hmac_key = b"1234"
        with open("config.json", "w") as fp:
            fp.write('{"hmac-key": "1234"}')

        # run in subprocess
        fn = main.main
        p = multiprocessing.Process(target=fn)
        p.start()
        self.add_cleanup(p.kill)
        # wait for the port to be ready
        addr = socket.getaddrinfo("localhost", main.PORT)[0][-1]
        with socket.socket() as sss:
            connect_or_retry(sss, addr, 10)
            ss = sss.makefile("rwb", 0)
            m1 = ss.readline()
            sjm = SignedJsonMessage.from_string(m1.decode("utf-8"), hmac_key)
            self.assertEqual(
                sjm.payload,
                {"version": 1, "api": "opener"})
            sjm2 = SignedJsonMessage(hmac_key, sjm.nonce)
            sjm2.set_payload({"cmd": "open"})
            ss.write(str(sjm2).encode("utf-8") + b"\n")
            ss.flush()
            m2 = ss.readline()
            sjm3 = SignedJsonMessage.from_string(
                m2.decode("utf-8"), hmac_key, sjm.nonce)
            self.assertEqual(sjm3.payload, {"status": "ok"})
            # XXX: test that the socket gets closed
        for i in range(20):
            if os.path.exists("pin21.value"):
                break
            time.sleep(0.1)
        with open("pin21.value") as fp:
            content = fp.readlines()
        self.assertEqual(content, ["1\n", "0\n"])
