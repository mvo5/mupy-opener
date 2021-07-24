#!/usr/bin/python3

import socket

from main import (
    send_with_hmac,
    recv_with_hmac,
)
from boot import read_config
from sjm import SignedJsonMessage

HOST = "opener"
PORT = 8877


def open():
    cfg = read_config()
    key = cfg["hmac-key"].encode("ascii")

    so = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    so.connect((HOST, PORT))
    so = so.makefile("rwb", 0)
    m1 = so.readline()
    # print(m1)
    sjm = SignedJsonMessage.from_string(
        m1.decode("utf-8"), key, expected_nonce=None)
    if sjm.payload != {"api": "opener", "version": 1}:
        raise Exception("unexpected payload %s" % str(sjm))
    # send open command
    send_with_hmac(so, key, sjm.nonce, {"cmd": "open"})
    msg = recv_with_hmac(so, key, sjm.nonce)
    if msg["status"] != "ok":
        raise Exception("unknown status in %s" % msg)


if __name__ == "__main__":
    open()
