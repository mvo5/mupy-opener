#!/usr/bin/python3
import io
import subprocess
import qrcode

from boot import read_config


if __name__ == "__main__":
    # read full config (including defaults)
    full_cfg = read_config()
    # only show the relevant subset for the app to scan
    cfg = {
        "hostname": full_cfg["hostname"],
        "hmac-key": full_cfg["hmac-key"],
    }
    qr = qrcode.QRCode()
    qr.add_data(cfg)
    qr.make(fit=True)
    print("hmac-key, import to smartphone")
    qr.print_ascii()
    img = qr.make_image()
    p = subprocess.Popen(["display", "-"], stdin=subprocess.PIPE)
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format="PNG")
    p.communicate(input=img_byte_arr.getvalue())
    p.wait()
