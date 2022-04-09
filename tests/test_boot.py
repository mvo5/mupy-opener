from unittest.mock import patch

from tests.test_base import BaseTest

# the actual code to be tested
import boot
import mock.network


class TestBoot(BaseTest):
    @patch("builtins.print")
    def test_boot_no_network_config_prints_warning(self, mocked_printf):
        boot.boot()
        self.assertEqual(mocked_printf.call_count, 2)
        self.assertRegex(
            mocked_printf.mock_calls[0].args[0],
            "cannot read config.json:.* No such file or directory.*",
        )
        self.assertRegex(
            mocked_printf.mock_calls[1].args[0],
            "no network config found, set via config.json ssid/key",
        )

    @patch("builtins.print")
    def test_boot_bad_network_config_prints_warning(self, mocked_printf):
        with open("config.json", "w") as fp:
            fp.write("not json")
        boot.boot()
        self.assertEqual(mocked_printf.call_count, 2)
        self.assertRegex(
            mocked_printf.mock_calls[0].args[0],
            r"cannot read config.json:.* Expecting value: line 1.*",
        )
        self.assertRegex(
            mocked_printf.mock_calls[1].args[0],
            r"no network config found, set via config.json ssid/key",
        )

    @patch("builtins.print")
    def test_boot_network_config(self, mocked_printf):
        with open("config.json", "w") as fp:
            hmac_key = "12345678901234567890123456789012"
            fp.write(
                '{"ssid":"some-ssid", "key":"some-key", ' '"hmac-key":"%s"}' % hmac_key
            )
        # XXX: use magicMock here instead of network.mock
        boot.boot()
        self.assertEqual(mocked_printf.call_count, 1)
        self.assertRegex(
            mocked_printf.mock_calls[0].args[0],
            r"connected as 192.168.0.4 \(opener\) to some-ssid",
        )
        # config is correct
        self.assertTrue(mock.network._mock_wlan_nic._active)
        self.assertEqual(mock.network._mock_wlan_nic._dhcp_hostname, "opener")
        self.assertEqual(
            mock.network._mock_wlan_nic._connect_to, ("some-ssid", "some-key")
        )
