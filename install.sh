#!/bin/sh

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
# XXX2: move to lib/ ?
# get hmac from external
mkdir -p lib
(cd lib ; 
  wget -c https://raw.githubusercontent.com/micropython/micropython-lib/master/python-stdlib/hmac/hmac.py ; 
  wget -c https://raw.githubusercontent.com/micropython/micropython-lib/master/python-stdlib/warnings/warnings.py ;
)
mkdir -p lib/hashlib
(cd lib/hashlib;
 wget -c https://raw.githubusercontent.com/micropython/micropython-lib/master/python-stdlib/hashlib/hashlib/__init__.py ;
   wget -c https://raw.githubusercontent.com/micropython/micropython-lib/master/python-stdlib/hashlib/hashlib/_sha224.py ;
   wget -c https://raw.githubusercontent.com/micropython/micropython-lib/master/python-stdlib/hashlib/hashlib/_sha256.py ;
   wget -c https://raw.githubusercontent.com/micropython/micropython-lib/master/python-stdlib/hashlib/hashlib/_sha384.py ;
   wget -c https://raw.githubusercontent.com/micropython/micropython-lib/master/python-stdlib/hashlib/hashlib/_sha512.py ;
)

# upload the file
for f in *.py lib/ config.json; do
    ampy put $f
done

echo "files uploaded, new dir content:"
ampy ls

echo "please reset device now"
