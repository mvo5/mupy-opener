import sys
import time
import _thread

is_micropython = (sys.implementation.name == "micropython")

if not is_micropython:
    import binascii
    import json
    import socket
    from mock import machine
    import mock.uos as os
else:
    import binascii
    import json
    import os
    import socket
    import machine


from sjm import SignedJsonMessage
from utgbot import TelegramBot


# available if defined in the config
telegram_bot = TelegramBot()

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
    pin = machine.Pin(pin, machine.Pin.OUT)
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
    # XXX: use generic log method
    telegram_bot.send("mupy-opener initialized")
    while True:
        conn, addr = s.accept()
        # run tg msg async to not block main data exchange
        _thread.start_new_thread(
            telegram_bot.send, ("connection from  {}".format(addr), ))
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
        # log event
        telegram_bot.send("door opened by {}".format(addr))
        # done
        conn.close()


def read_config():
    with open("config.json") as f:
        return json.load(f)


def main():
    with open("config.json") as f:
        cfg = json.load(f)
    hmac_key = cfg.get("hmac-key").encode("ascii")
    # init bot
    telegram_bot_token = cfg.get("telegram-bot-token")
    telegram_chat_id = cfg.get("telegram-chat-id")
    if telegram_bot_token and telegram_chat_id:
        print("connecting telegram bot")
        telegram_bot.config(telegram_bot_token, telegram_chat_id)

    # print("using key", hmac_key)
    if not hmac_key:
        # generated with: dd if=/dev/random count=32 bs=1 | base64
        print("no hmac-key set, please generate a strong 32byte key")
        return
    # This should be at least 128bit of real randomness
    if len(hmac_key) < 16:
        print("hmac key {} should not be too short".format(hmac_key))
        return

    # main execution loop - any (uncaught) error here will trigger a
    # reboot to ensure the machine is always available
    try:
        wait_for_commands(hmac_key, PORT)
    except KeyboardInterrupt:
        raise
    except Exception as e:
        # XXX: try logging via tg?
        print("reboot from exception in wait_for_commands: {}".format(e))
        machine.reset()


if __name__ == "__main__":
    main()
