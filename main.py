import errno
import sys
import time

is_micropython = sys.implementation.name == "micropython"

if not is_micropython:
    import binascii
    import socket
    from mock import machine
    import mock.gc as gc
    import mock.uos as os
    import mock.usys as usys
else:
    import binascii
    import gc
    import os
    import socket
    import machine
    import usys


from config import read_config
from sjm import SignedJsonMessage
from utgbot import TelegramBot


# available if defined in the config
telegram_bot = TelegramBot()

# will be overriden with a handler on the fs
last_crash_fp = usys.stderr

# tcp port to listen on
PORT = 8877
# opener wait in sec
OPENER_WAIT = 1


def tg_log(msg):
    if not msg:
        return
    print("tg_log: {}".format(msg))
    # retry sending up to 3 times
    for i in range(3):
        try:
            if telegram_bot.send(msg):
                break
        except Exception as e:
            time.sleep(1)
            print("cannot sent to tg, retrying: {}".format(e))


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


def readline_until_non_empty(so):
    while True:
        msg = so.readline()
        if msg:
            return msg


def recv_with_hmac(so, key, nonce):
    # sometimes we get an empty readline message here, discard that and
    # read until there is actual data
    msg = readline_until_non_empty(so)
    sjm = SignedJsonMessage.from_string(msg.decode("utf-8"), key, nonce)
    return sjm.payload


def wait_for_commands(key, hostname, port, opener_pin):
    # XXX: why pick the last one?
    addr = socket.getaddrinfo("0.0.0.0", port)[0][-1]
    device_info = "unknown"
    s = socket.socket()
    # ensure no TIME_WAIT issues after socket closing
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # socket wait will timeout every 5s
    s.settimeout(5.0)
    s.bind(addr)
    s.listen(5)
    tg_log(
        "mupy-opener listening on {} port {} (reset cause: {})".format(
            hostname, port, machine.reset_cause()
        )
    )

    # watchdog timeout for 30s
    wdt = machine.WDT(timeout=30000)
    while True:
        wdt.feed()
        try:
            conn, addr = s.accept()
        except OSError as e:
            # this will feed the watchgod every 5s
            if e.errno == errno.ETIMEDOUT:
                continue
            raise
        # No tg_log() here to avoid delaying processing of the commands,
        # also no _thread.start_new_thread() because that is too memory
        # hungry on the esp32
        print("connection on {} from {}".format(hostname, addr))
        # XXX: add integration test that checks if it really timeouts
        conn.settimeout(5.0)
        # only binary data is supported by micropython
        f = conn.makefile("rwb", 0)
        # securely generate session nonce
        nonce = gen_nonce()
        try:
            send_with_hmac(f, key, nonce, {"version": 1, "api": "opener"})
        except Exception as e:
            tg_log("cannot send helo on {}: {} to {}".format(hostname, e, addr))
            f.close()
            conn.close()
            continue
        # we expect a command next
        try:
            cmd = recv_with_hmac(f, key, nonce)
        except Exception as e:
            tg_log("cannot recv cmd on {}: {} from {}".format(hostname, e, addr))
            f.close()
            conn.close()
            continue
        # accept command
        if cmd.get("cmd") == "open":
            device_info = cmd.get("device-info")
            toogle_pin(opener_pin)
            try:
                send_with_hmac(f, key, nonce, {"status": "ok"})
            except Exception as e:
                tg_log("cannot send status on {}: {} to {}".format(hostname, e, addr))
                f.close()
                conn.close()
                continue
        else:
            err = '{"error": "unknown command {}"}\n'.format(cmd)
            tg_log("unknown command on {} in {} from {}".format(hostname, cmd, addr))
            f.write(err.encode("ascii"))
            f.close()
            conn.close()
            continue
        # done
        f.close()
        conn.close()
        # log event
        tg_log(
            "door on {} opened by {} {} (mem {})".format(
                hostname, device_info, addr, gc.mem_free()
            )
        )
        # clean GC (robustness)
        gc.collect()


def main():
    cfg = read_config()
    # init bot
    telegram_bot_token = cfg.get("telegram-bot-token")
    telegram_chat_id = cfg.get("telegram-chat-id")
    if telegram_bot_token and telegram_chat_id:
        print("connecting telegram bot")
        telegram_bot.config(telegram_bot_token, telegram_chat_id)
    # hostname
    hostname = cfg.get("hostname")
    # gpio pin that is used
    opener_pin = cfg.get("opener-gpio-pin", 21)
    # hmac-key
    hmac_key = cfg.get("hmac-key").encode("ascii")
    if not hmac_key:
        # generated with: dd if=/dev/random count=32 bs=1 | base64
        print("no hmac-key set, please generate a strong 32byte key")
        return
    # This should be at least 128bit of real randomness
    if len(hmac_key) < 16:
        print("hmac key {} should not be too short".format(hmac_key))
        return

    try:
        with open("last-crash.log") as fp:
            log = fp.read()
            tg_log(log)
    except OSError as e:
        if e.errno != 2:  # ENOENT
            tg_log("cannot open last-crash.log: {}".format(e))

    global last_crash_fp
    last_crash_fp = open("last-crash.log", "w")

    # main execution loop - any (uncaught) error here will trigger a
    # reboot to ensure the machine is always available
    try:
        wait_for_commands(hmac_key, hostname, PORT, opener_pin)
    except KeyboardInterrupt:
        raise
    except Exception as e:
        # log to last-crash file
        last_crash_fp.seek(0, 0)
        usys.print_exception(e, last_crash_fp)
        last_crash_fp.flush()
        last_crash_fp.close()
        # log to screen
        print("reboot from exception in wait_for_commands:")
        usys.print_exception(e)
        machine.reset()


if __name__ == "__main__":
    main()
