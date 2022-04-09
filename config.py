import sys

is_micropython = sys.implementation.name == "micropython"

import json

# current default config
default_cfg = {
    # network config
    "ssid": "",
    "key": "",
    "hostname": "opener",
}

# XXX: json is a terrible way to do configs but it's part of the
# reference lib


def read_config():
    cfg = default_cfg.copy()
    try:
        with open("config.json") as f:
            # merge with default config
            cfg.update(json.load(f))
    except Exception as e:
        print("cannot read config.json: {}".format(e))
    return cfg
