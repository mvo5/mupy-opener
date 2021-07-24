
# mock some consts
STA_IF = "STA_IF"


_mock_wlan_nic = None


def WLAN(mode):
    global _mock_wlan_nic
    _mock_wlan_nic = MockWlanNic()
    return _mock_wlan_nic


class MockWlanNic:
    def __init__(self):
        self._isconnected = 0
        self._active = False
        self._dhcp_hostname = "unset"

    def isconnected(self):
        self._isconnected += 1
        return self._isconnected > 2

    def active(self, v):
        self._active = v

    def config(self, dhcp_hostname=""):
        assert self._active
        self._dhcp_hostname = dhcp_hostname

    def connect(self, ssid, key):
        assert self._active
        self._connect_to = (ssid, key)

    def ifconfig(self):
        assert self._active
        return ("192.168.0.4", "255.255.255.0", "192.168.0.1", "8.8.8.8")
