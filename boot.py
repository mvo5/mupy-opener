import sys

is_micropython = sys.implementation.name == "micropython"

if not is_micropython:
    import mock.machine as machine
    import mock.network as network
else:
    import machine
    import network

from config import read_config


def connect_wlan(ssid, key, hostname):
    wlan = network.WLAN(network.STA_IF)
    # needs to be set active before *anything* can be done here
    wlan.active(True)
    wlan.config(dhcp_hostname=hostname)
    if not wlan.isconnected():
        wlan.connect(ssid, key)
        while not wlan.isconnected():
            # save power while waiting
            machine.idle()
    ip = wlan.ifconfig()[0]
    return ip


def boot():
    cfg = read_config()
    if cfg.get("ssid", "") == "":
        print("no network config found, set via config.json ssid/key")
        return
    # connect wlan
    ip = connect_wlan(cfg["ssid"], cfg["key"], cfg["hostname"])
    print("connected as {} ({}) to {}".format(ip, cfg["hostname"], cfg["ssid"]))


if __name__ == "__main__":
    boot()
