#!/bin/sh

set -e

# XXX: have setup.py instead?

# XXX: replace ampy with micropython 1.16 new tool (mremote?)
if ! ampy >/dev/null; then
    echo "Need ampy, please install using 'pip install adafruit-ampy'"
    exit 1
fi
if ! test -f .ampy; then
    echo "please setup .ampy file, see https://github.com/scientifichackers/ampy#configuration"
    exit 1
fi
. $(pwd)/.ampy
if ! test -w "$AMPY_PORT"; then
    echo "cannot write to the $AMPY_PORT"
    exit 1
fi

# XXX: terrible, use micropython pip instead
# get hmac from external
mkdir -p lib
(cd lib ; 
  wget -c -O mvourequests.py https://raw.githubusercontent.com/mvo5/micropython-lib/urequests-simple-timeout/python-ecosys/urequests/urequests.py;
)

# upload the file
for f in *.py lib/ config.json; do
    ampy put $f
done

echo "files uploaded, new dir content:"
ampy ls

echo "please reset device now"
