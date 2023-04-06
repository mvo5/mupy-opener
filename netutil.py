from sjm import SignedJsonMessage


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
