#!/usr/bin/python3

import socket
import sys
import time

is_micropython = sys.implementation.name == "micropython"

if is_micropython:
    import micropython
    from machine import Pin

from netutil import send_with_hmac, recv_with_hmac
from config import read_config
from sjm import SignedJsonMessage

PORT = 8877


def open():
    # TODO: add tg_log here
    if len(sys.argv) > 1:
        cfg = read_config(sys.argv[1])
    else:
        cfg = read_config()
    key = cfg["hmac-key"].encode("ascii")
    hostname = cfg["hostname"]

    so = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    so.connect((hostname, PORT))
    so = so.makefile("rwb", 0)
    m1 = so.readline()
    # print(m1)
    sjm = SignedJsonMessage.from_string(m1.decode("utf-8"), key, expected_nonce=None)
    if sjm.payload != {"api": "opener", "version": 1}:
        raise Exception("unexpected payload %s" % str(sjm.payload))
    # send open command
    if is_micropython:
        device_info = "mupy-open-gadget"
    else:
        device_info = socket.gethostname()
    cmd_json = {"cmd": "open", "device-info": device_info}
    send_with_hmac(so, key, sjm.nonce, cmd_json)
    msg = recv_with_hmac(so, key, sjm.nonce)
    if msg["status"] != "ok":
        raise Exception("unknown status in %s" % msg)


def micropython_main():
    # make this configurable
    BUTTON_PIN = 39
    button = Pin(BUTTON_PIN, Pin.IN)
    pressed=0
    while True:
        if button.value() == 0:
            print("pressed")
            pressed += 1
        else:
            # 1s = 20*50ms
            if pressed > 20:
                open()
            pressed = 0
        time.sleep_ms(50)


if __name__ == "__main__":
    if is_micropython:
        micropython_main()
    else:
        open()
