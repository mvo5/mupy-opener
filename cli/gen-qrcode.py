#!/usr/bin/python3
import io
import subprocess
import qrcode

from boot import read_config


if __name__ == "__main__":
    cfg = read_config()

    qr = qrcode.QRCode(
        box_size=10,
        border=4,
    )
    qr.add_data(cfg["hmac-key"].encode("ascii"))
    qr.make(fit=True)
    print("hmac-key, import to smartphone")
    qr.print_ascii()
    img = qr.make_image()
    p = subprocess.Popen(["display", "-"], stdin=subprocess.PIPE)
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format="PNG")
    p.communicate(input=img_byte_arr.getvalue())
    p.wait()
