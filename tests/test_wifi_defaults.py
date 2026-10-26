from pathlib import Path
import subprocess
import tempfile
import unittest

from test_build_checks import BASH, REPO


@unittest.skipUnless(BASH, "需要 Bash")
class WifiDefaultsTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="r619ac-wifi-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.template = self.root / "package/network/config/wifi-scripts/files/lib/wifi/mac80211.uc"
        self.template.parent.mkdir(parents=True)
        self.original = '''if (radio_exists(phy.path, macaddr, phy_name, radio.index))
	continue;
print(`set ${s}=wifi-device
set ${s}.type='mac80211'
set ${si}.mode='ap'
set ${si}.ssid='${defaults?.ssid || "OpenWrt"}'
set ${si}.encryption='${defaults?.encryption || encryption}'
set ${si}.key='${defaults?.key || ""}'
set ${si}.disabled='${defaults ? 0 : 1}'

`);
'''
        self.template.write_text(self.original, encoding="utf-8", newline="\n")

    def apply_patch(self):
        return subprocess.run(
            [BASH, "-c", 'patch --batch --forward --fuzz=0 -p1 < "$1"', "test",
             (REPO / "patches/openwrt/100-enable-default-wifi.patch").as_posix()],
            cwd=self.root, capture_output=True, encoding="utf-8", errors="replace", timeout=15,
        )

    def test_only_new_wifi_disabled_default_changes(self):
        result = self.apply_patch()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        actual = self.template.read_text(encoding="utf-8")
        expected = self.original.replace("set ${si}.disabled='${defaults ? 0 : 1}'",
                                         "set ${si}.disabled='0'")
        self.assertEqual(actual, expected)
        self.assertLess(actual.index("radio_exists("), actual.index("print(`"))
        self.assertIn("\tcontinue;", actual)

    def test_changed_upstream_template_is_rejected(self):
        changed = self.original.replace("set ${si}.disabled='${defaults ? 0 : 1}'",
                                        "set ${si}.disabled='1'")
        self.template.write_text(changed, encoding="utf-8", newline="\n")
        self.assertNotEqual(self.apply_patch().returncode, 0)
        self.assertEqual(self.template.read_text(encoding="utf-8"), changed)


if __name__ == "__main__":
    unittest.main()
