
def idle():
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
