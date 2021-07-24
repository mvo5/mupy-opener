import sys
import time

is_micropython = (sys.implementation.name == "micropython")

if not is_micropython:
    import binascii
    import json
    import socket
    from mock.machine import Pin
    import mock.uos as os
else:
    import binascii
    import json
    import os
    import socket
    from machine import Pin

from sjm import SignedJsonMessage

# XXX: make all this configurable in config.json
# default port we listen to
PORT = 8877
# gpio pin to open
OPENER_PIN = 21
# opener wait in sec
OPENER_WAIT = 1


def gen_nonce():
    return binascii.b2a_base64(os.urandom(32)).strip().decode("ascii")


def toogle_pin(pin):
    pin = Pin(pin, Pin.OUT)
    pin.value(1)
    time.sleep(OPENER_WAIT)
    pin.value(0)


def send_with_hmac(so, key, nonce, msg):
    sjm = SignedJsonMessage(key, nonce)
    sjm.set_payload(msg)
    so.write(str(sjm).encode("utf-8") + b"\n")


def recv_with_hmac(so, key, nonce):
    msg = so.readline()
    sjm = SignedJsonMessage.from_string(msg.decode("utf-8"), key, nonce)
    return sjm.payload


def wait_for_commands(key, port):
    # XXX: why pick the last one?
    addr = socket.getaddrinfo("0.0.0.0", port)[0][-1]
    s = socket.socket()
    s.bind(addr)
    s.listen(1)
    print("listening on {}".format(addr))
    while True:
        conn, addr = s.accept()
        # XXX: send (async) to telegram for logging
        print("connection from {}".format(addr))
        # XXX: add integration test that checks if it really timeouts
        conn.settimeout(5.0)
        # only binary data is supported by micropython
        f = conn.makefile("rwb", 0)
        # send header, nonce and hmac
        nonce = gen_nonce()
        try:
            send_with_hmac(f, key, nonce, {"version": 1, "api": "opener"})
        except Exception as e:
            print(e)
            conn.close()
            continue
        # we expect a command next
        try:
            cmd = recv_with_hmac(f, key, nonce)
        except Exception as e:
            print(e)
            conn.close()
            continue
        # accept command
        if cmd.get("cmd") == "open":
            toogle_pin(OPENER_PIN)
            try:
                send_with_hmac(f, key, nonce, {"status": "ok"})
            except Exception as e:
                print(e)
                conn.close()
                continue
        else:
            err = '{"error": "unknown command %s"}\n' % cmd
            print(err)
            f.write(err.encode("ascii"))
        # done
        conn.close()


def read_config():
    with open("config.json") as f:
        return json.load(f)


def main():
    with open("config.json") as f:
        cfg = json.load(f)
    hmac_key = cfg.get("hmac-key").encode("ascii")
    # print("using key", hmac_key)
    if not hmac_key:
        # generated with: dd if=/dev/random count=32 bs=1 | base64
        print("no hmac-key set, please generate a strong 32byte key")
        return
    # if len(hmac_key) < 20:
    #     print("hmac key {} should be 32 chars".format(hmac_key))
    #     return
    wait_for_commands(hmac_key, PORT)


if __name__ == "__main__":
    main()
