
def idle():
    pass


def reset():
    pass


class Pin:
    IN = "in"
    OUT = "out"

    def __init__(self, nr, direction):
        self._nr = nr
        self._direction = direction

    def value(self, v):
        self._v = v
        with open("pin{}.value".format(self._nr), "a") as fp:
            fp.write("{}\n".format(v))


class WDT:
    def __init__(self, id=0, timeout=2000):
        self._timeout = timeout
        self._feed = 0

    def feed(self):
        self._feed += 1
        with open("wdt.log", "w") as fp:
            fp.write("{}".format(self._feed))
