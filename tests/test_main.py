import json
import multiprocessing
import os
import random
import socket
import time

from unittest.mock import patch

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

    def setUp(self):
        super().setUp()
        # XXX: restore value
        main.OPENER_WAIT = 0.0001
        main.PORT = random.randrange(5000, 60000)
        # mock config
        self.hmac_key = b"01234567890123456789"
        mock_conf = {
            "hmac-key": self.hmac_key.decode("utf-8"),
            "telegram-bot-token": "111:token",
            "telegram-chat-id": "1234",
        }
        with open("config.json", "w") as fp:
            fp.write(json.dumps(mock_conf))

    @patch("main.tg_log")
    def test_main_integration_runthrough(self, mock_tg_send):
        tg_bot_send_q = multiprocessing.Queue()
        mock_tg_send.side_effect = lambda *args: tg_bot_send_q.put(*args)
        # run "main" in subprocess, no mocking will work
        fn = main.main
        p = multiprocessing.Process(target=fn)
        p.start()
        self.add_cleanup(p.kill)
        # wait for the port to be ready
        addr = socket.getaddrinfo("localhost", main.PORT)[0][-1]
        with socket.socket() as sss:
            connect_or_retry(sss, addr, 10)
            self.assertRegex(
                tg_bot_send_q.get(), r'mupy-opener listening on port [0-9]+')
            ss = sss.makefile("rwb", 0)
            m1 = ss.readline()
            sjm = SignedJsonMessage.from_string(
                m1.decode("utf-8"), self.hmac_key)
            self.assertEqual(
                sjm.payload,
                {"version": 1, "api": "opener"})
            sjm2 = SignedJsonMessage(self.hmac_key, sjm.nonce)
            sjm2.set_payload({"cmd": "open"})
            ss.write(str(sjm2).encode("utf-8") + b"\n")
            ss.flush()
            m2 = ss.readline()
            sjm3 = SignedJsonMessage.from_string(
                m2.decode("utf-8"), self.hmac_key, sjm.nonce)
            self.assertEqual(sjm3.payload, {"status": "ok"})
            self.assertRegex(tg_bot_send_q.get(), r'door opened by .*')
            # XXX: test that the socket gets closed
        for i in range(20):
            if os.path.exists("pin21.value"):
                break
            time.sleep(0.5)
        # ensure ping value was written
        with open("pin21.value") as fp:
            self.assertEqual(fp.readlines(), ["1\n", "0\n"])
        # ensure watchdog timer was triggered
        with open("wdt.log") as fp:
            self.assertEqual(fp.read(), "2")

    @patch("socket.socket")
    def test_main_handles_exception(self, mock_socket):
        mock_socket.side_effect = Exception("fake exception")
        main.main()
        with open("last-crash.log") as fp:
            self.assertEqual(fp.read(), "fake exception\n")
