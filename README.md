# Opener in micropython for ESP32

This repo provides a micropython application that can run on the ESP32
(but this could be ported to a raspberry pi as well) as a small TCP
service that allows to trigger actions based on signed json
messages. The code and framework is flexible and easy to extend.

However (due to YAGNI) it currently only implements the main use-case:
set a pin to "high" for 1 sec to close a relay that will open a garage
door.

There is a CLI python program to trigger the opening and a matching
android app as well.

## Install

Install micropython on your device. Then create a .ampy file (if you
don't have one already) with something like:
```
export AMPY_PORT=/dev/ttyUSB0
```

Then create a `config.json` with your configuration, something like:
```
{
    "ssid": "my-wlan",
    "key": "my-key",
    "hostname": "opener",

    "telegram-bot-token": "123:asfsdfa",
    "telegram-chat-id": "1234",

    "opener-gpio-pin": 21,

    "hmac-key": "generate with e.g. dd if=/dev/random count=32 bs=1 | base64"
}
```

and place it in the source dir. Then run `install.sh` and all the
files will get uploaded to the esp32. The hmac-key should be big
enough, 32 bytes of randomness (128bit) should be fine here.

You can use the `cli/gen-qrcode` binary to import the shared secret
into your smartphone. The smartphone app is availalbe on:
https://play.google.com/store/apps/details?id=de.int10.muopener

You can also use the open.py example:
```
$ PYTHONPATH=. python3 ./cli/open.py
```
to open.

## Update

To update, just run `install.sh` again - but one side effect of
running the watchdog timer (see below) is that to reflash via
`install.sh` one may need to interrupt the esp32 boot very early via
e.g. `screen /dev/ttyUSB0 115200` and then `ctrl-c` in there to avoid
the watchdog from getting triggered. After that the `install.sh` will
work normally.

### Telegram support

The system can send telegram message to monitor the status of
the system. You can create your own personal bot with the
botfather and then store the secret token inside the config.
The chat-id of the target user is also required, it's possible
to obtain that by asking the @RawDataBot about it. Also make
sure that start a chat with your bot first, otherwise no
messages will arrive.

## Protocol

The protocol between esp32 and app is based on hmac signed json
message. The message format is heavily inspired by the JWT design. It
uses a shared secret that can be imported to the android app via a QR
code. There is no encryption, so only authenticity and integrity is
ensured, not confidentiality. The protocol could be extended to
support this but a) YAGNI b) there is nothing secret currently in
these messages.

Each message contains a header with the sign algoirthm used (but only
HMAC-sha256 is implemented right now), the version of the protocol
("1" right now) and a "nonce". Then the json payload and finally the
signature. All parts are base64 encoded and concatenated with "." as
the separator.

The protocol itself is stateful and line oriented. When a client
connects the esp32 sends a "welcome" message that contains the version
and the supported api. Only the "opener" API is supported today (but it
would be trivial to extend).  In the header it also contains the
randomly generated nonce that is valid *only* for this session. The
client then validates the signature and uses the nonce for all
subsequent calls. The client makes API calls as json and the server
replies with json message as needed.

## Testing

Run
```
python3 -m unittest
```

to run the unit and integration tests.  The tests will run with the
normal python3 and some of the features of micropython not available
are mocked (e.g. `import machine`). This is not perfect as there are
some differences between python/micropython. E.g. micropython has no
`socket.makefile("rw")`, it only suports binary unbuffered sockets. It
would be nice to explore if the unix port of micropython could be used
to run the unittest. For "sjm.py" at least you can run:
```
$ MICROPYPATH=./lib micropython ./sjm.py
```
to do some manual checks.

## Robustness

The code was written with the goal that it should never go into
a state where the opener will stop responding. This means that
any uncaught exceptions are logged in `last-crash.log` and then
the machine is restarted. In additon a watchdog timer is setup
and it will trigger a reboot after 30s hang.


## Design considerations

Some design consierations:
1. security must be good enough to trust it opening a garage door
1. everything must be simple enough to run on a esp32

