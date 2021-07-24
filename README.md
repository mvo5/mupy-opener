# Opener in micropython for ESP32

This repo provides a micropython application that can run on the ESP32
(but this could be run on a raspberry pi as well) as a small TCP
service that allows to trigger actions based on signed json
messages. The code and framework is flexible and easy to extend.

However (due to YAGNI) it currently only implements the main use-case:
set a pin to "high" for 1sec to close a relay that will open a garage
door.

There is a CLI python program to trigger the opening and a matching
android app as well.

## Protocol

The protocol between esp32 and app is based on hmac signed json
message. The message format is heavily inspired by the JWT design. It
uses a shared secret that can be imported to the android app via a QR
code. There is no encryption, so only authenticity and integrity is
ensured, not confidentiality. The protocol could be extended to
support this but a) YAGNI b) there is nothing secret currently in
these messages.

Each message contains a header with the sign algoirthm used (but only
HMAC-sha512 is implemented right now), the version of the protocol
("1" right now) and a "nonce". Then the json payload and finally the
signature. All parts are base64 encoded and concatenated with "." as
the separator.

The protocol itself is stateful and line oriented. When a client
connects the esp32 sends a "welcome" message that contains the version
and the supported api. Only the "opener" API is supported today but it
would be trivial to extend.  In the header it also contains the
randomly generated nonce that is valid *only* for this session. The
client then validates the signature and uses the nonce for all
subsequent calls. The clientmakes API calls as json and the server
replies with json message as needed.

## Install

Install micropython on your device. Then create a .ampy file (if you
don't have one already) with something like:
```
export AMPY_PORT=/dev/ttyUSB0
```

Then create a config.json with your configuration, something like:
```
{
    "ssid": "my-wlan",
    "key": "my-key",
    "hostname": "opener",
    
    "hmac-key": "generate with e.g. dd if=/dev/random count=32 bs=1 | base64"
}
```

and place it in the source dir. Then run `install.sh` and all the
files will get uploaded to the esp32. The hmac-key should be big
enough, 32 bytes of randomness (128bit) are plenty here.

You can use the `cli/gen-qrcode` binary to import the shared secret
into your smartphone. You can also use the open.py example:
```
$ PYTHONPATH=. python3 ./cli/open.py
```
to open.


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


## Design considerations

Some design consierations:
1. security must be good enough to trust it opening a garage door
1. everything must be simple enough to run on a esp32



