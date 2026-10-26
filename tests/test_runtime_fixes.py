import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from test_build_checks import BASH, REPO


@unittest.skipUnless(BASH, "需要 Bash")
class RuntimeFixesTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="r619ac-runtime-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.shell_root = subprocess.check_output(
            [BASH, "-c", 'cd -- "$1"\npwd', "test", self.root.as_posix()],
            encoding="utf-8", timeout=10,
        ).strip()
        self.mounts = self.write("mounts", "")
        source = (REPO / "files/usr/libexec/r619ac-storage-guard.sh").read_text(encoding="utf-8")
        source = source.replace("/proc/self/mounts", f"{self.shell_root}/mounts")
        source = source.replace("/mnt", f"{self.shell_root}/mnt")
        source = source.replace("/media", f"{self.shell_root}/media")
        self.guard = self.write("guard.sh", source)

    def write(self, name, content):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8", newline="\n")
        return path

    def shell(self, code, *args, stdin=None):
        return subprocess.run(
            [BASH, "-c", code, "test", *args], input=stdin,
            capture_output=True, encoding="utf-8", errors="replace", timeout=15,
        )

    def disk(self, filesystem="ext4", options="rw,relatime", name="sda1"):
        (self.root / "mnt" / name).mkdir(parents=True, exist_ok=True)
        mount = f"{self.shell_root}/mnt/{name}"
        escaped_mount = mount.replace(" ", "\\040")
        self.write("mounts", f"/dev/sda2 {escaped_mount} {filesystem} {options} 0 0\n")
        return mount

    def check_path(self, path):
        return self.shell('. "$1"\nr619ac_storage_ready "$2"', self.guard.as_posix(), path)

    def test_missing_mount_is_rejected_without_creating_directory(self):
        (self.root / "mnt/sda1").mkdir(parents=True)
        result = self.check_path(f"{self.shell_root}/mnt/sda1/transmission/.config")
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.root / "mnt/sda1/transmission").exists())

    def test_missing_disk_directory_is_rejected(self):
        self.assertNotEqual(self.check_path(f"{self.shell_root}/mnt/sda1/downloads").returncode, 0)

    def test_rw_disk_accepts_new_nested_download_directory(self):
        mount = self.disk()
        result = self.check_path(f"{mount}/new/downloads")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((self.root / "mnt/sda1/new").exists())

    def test_exfat_disk_is_accepted(self):
        self.assertEqual(self.check_path(self.disk(filesystem="exfat") + "/downloads").returncode, 0)

    def test_readonly_disk_is_rejected(self):
        self.assertNotEqual(self.check_path(self.disk(options="ro,relatime") + "/downloads").returncode, 0)

    def test_ram_or_internal_filesystem_is_rejected(self):
        for filesystem in ("overlay", "squashfs", "tmpfs", "rootfs", "ramfs", "ubifs", "jffs2"):
            with self.subTest(filesystem=filesystem):
                self.assertNotEqual(self.check_path(self.disk(filesystem=filesystem) + "/downloads").returncode, 0)

    def test_neighbor_mount_does_not_count(self):
        self.disk(name="sda10")
        (self.root / "mnt/sda1").mkdir()
        self.assertNotEqual(self.check_path(f"{self.shell_root}/mnt/sda1/downloads").returncode, 0)

    def test_mount_name_with_space_is_accepted(self):
        self.assertEqual(self.check_path(self.disk(name="USB disk") + "/downloads").returncode, 0)

    def test_parent_traversal_is_rejected(self):
        self.assertNotEqual(self.check_path(self.disk() + "/../sda2/downloads").returncode, 0)

    def test_media_mount_is_accepted(self):
        (self.root / "media/disk").mkdir(parents=True)
        mount = f"{self.shell_root}/media/disk"
        self.write("mounts", f"/dev/sda1 {mount} ext4 rw,relatime 0 0\n")
        self.assertEqual(self.check_path(mount + "/downloads").returncode, 0)

    def test_ram_config_directory_is_unchanged(self):
        self.assertEqual(self.check_path("/var/etc/transmission").returncode, 0)

    @unittest.skipUnless(os.name == "posix", "真实符号链接逃逸在 Linux CI 中验证")
    def test_symlink_back_to_internal_storage_is_rejected(self):
        mount = self.disk()
        internal = self.root / "internal"
        internal.mkdir()
        (self.root / "mnt/sda1/downloads").symlink_to(internal, target_is_directory=True)
        self.assertNotEqual(self.check_path(mount + "/downloads/new").returncode, 0)

    def test_any_missing_storage_path_blocks_startup(self):
        mount = self.disk()
        code = '. "$1"\nshift\nlogger() { printf "%s\\n" "$*" >&2; }\nr619ac_require_storage "$@"'
        result = self.shell(code, self.guard.as_posix(), mount + "/downloads",
                            f"{self.shell_root}/mnt/absent/incomplete")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("拒绝启动", result.stderr)

    def run_firstboot(self):
        source = (REPO / "files/etc/uci-defaults/90-r619ac-runtime-fixes").read_text(encoding="utf-8")
        source = source.replace("/rom/etc/", "@ROM_ETC@/").replace("/etc/", "@ETC@/")
        source = source.replace("@ROM_ETC@", f"{self.shell_root}/rom/etc")
        source = source.replace("@ETC@", f"{self.shell_root}/etc")
        script = self.write("firstboot.sh", source)
        return subprocess.run([BASH, script.as_posix()], capture_output=True,
                              encoding="utf-8", errors="replace", timeout=15)

    def haproxy(self, modified=False):
        self.write("rom/etc/haproxy.cfg", "global\n  daemon\n")
        self.write("etc/haproxy.cfg", "custom\n" if modified else "global\n  daemon\n")
        service = self.write("etc/init.d/haproxy",
                             f'#!/bin/sh\nprintf "%s\\n" "$1" >> "{self.shell_root}/haproxy-actions"\n')
        service.chmod(0o755)

    def test_only_invalid_official_passwall_sources_are_removed(self):
        base = "https://downloads.openwrt.org/releases/25.12.6/packages/arm_cortex-a7_neon-vfpv4"
        keep = [base + "/base/packages.adb", base + "/luci/packages.adb",
                "https://packages.example.org/passwall_packages/packages.adb"]
        bad = [base + "/passwall_luci/packages.adb", base + "/passwall_packages/packages.adb"]
        source = self.write("etc/apk/repositories.d/distfeeds.list", "\n".join(keep + bad) + "\n")
        result = self.run_firstboot()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(source.read_text(encoding="utf-8").splitlines(), keep)
        self.assertEqual(self.run_firstboot().returncode, 0)
        self.assertEqual(source.read_text(encoding="utf-8").splitlines(), keep)

    def test_default_haproxy_is_stopped_and_disabled(self):
        self.haproxy()
        result = self.run_firstboot()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.root / "haproxy-actions").read_text().splitlines(), ["stop", "disable"])

    def test_valid_custom_repository_file_is_not_rewritten(self):
        source = self.write("etc/apk/repositories.d/customfeeds.list",
                            "https://packages.example.org/passwall_packages/packages.adb\n")
        os.utime(source, (946684800, 946684800))
        modified = source.stat().st_mtime_ns
        self.assertEqual(self.run_firstboot().returncode, 0)
        self.assertEqual(source.stat().st_mtime_ns, modified)

    def test_custom_haproxy_is_preserved(self):
        self.haproxy(modified=True)
        result = self.run_firstboot()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((self.root / "haproxy-actions").exists())
        self.assertEqual((self.root / "etc/haproxy.cfg").read_text(), "custom\n")

    def test_no_rom_haproxy_config_is_left_unchanged(self):
        self.haproxy()
        (self.root / "rom/etc/haproxy.cfg").unlink()
        self.assertEqual(self.run_firstboot().returncode, 0)
        self.assertFalse((self.root / "haproxy-actions").exists())


@unittest.skipUnless(BASH, "需要 Bash")
class PackagePatchesTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="r619ac-packages-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.samba = self.root / "feeds/packages/net/samba4/Makefile"
        self.samba.parent.mkdir(parents=True)
        self.samba.write_text(
            "# 上游软件包基线\ninclude $(TOPDIR)/rules.mk\n\n"
            "PKG_NAME:=samba\nPKG_VERSION:=4.22.7\nPKG_RELEASE:=3\n\n"
            "PKG_SOURCE:=$(PKG_NAME)-$(PKG_VERSION).tar.gz\nPKG_SOURCE_URL:= \\\n"
            "\t\thttps://ftp.gwdg.de/pub/samba/stable/ \\\n"
            "\t\thttps://ftp.heanet.ie/mirrors/ftp.samba.org/stable/ \\\n"
            "\t\thttps://ftp.riken.jp/net/samba/samba/stable/ \\\n"
            "\t\thttp://www.nic.funet.fi/index/samba/pub/samba/stable/ \\\n"
            "\t\thttp://samba.mirror.bit.nl/samba/ftp/stable/ \\\n"
            "\t\thttps://download.samba.org/pub/samba/stable/\n"
            "PKG_HASH:=12195811d4542f661536e9055b44d58c53020412beafaae205e227bf72f6a497\n\n"
            "PKG_BUILD_FLAGS:=gc-sections\n\n", encoding="utf-8", newline="\n")
        self.transmission = self.root / "feeds/packages/net/transmission/files/transmission.init"
        self.transmission.parent.mkdir(parents=True)
        (self.transmission.parent.parent / "Makefile").write_text(
            "PKG_NAME:=transmission\nPKG_VERSION:=4.1.3\nPKG_RELEASE:=1\n\n"
            "PKG_SOURCE:=$(PKG_NAME)-$(PKG_VERSION).tar.xz\n"
            "PKG_SOURCE_URL:=https://github.com/transmission/transmission/releases/download/$(PKG_VERSION)/\n",
            encoding="utf-8", newline="\n")
        self.transmission.write_text(
            'transmission() {\n\tlocal USE\n'
            '\t[ "$MEM" -gt 1 ] && USE=$((MEM * mem_percentage * 10))\n\n'
            '\tconfig_file="$config_dir/settings.json"\n'
            '\t[ -d "$config_dir" ] || {\n\t\tmkdir -p "$config_dir"\n\t}\n}\n',
            encoding="utf-8", newline="\n")

    def prepare(self):
        return subprocess.run([BASH, (REPO / "scripts/prepare-packages.sh").as_posix()],
                              cwd=self.root, capture_output=True, encoding="utf-8",
                              errors="replace", timeout=20)

    def test_package_patches_apply_and_guard_precedes_writes(self):
        result = self.prepare()
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        samba = self.samba.read_text(encoding="utf-8")
        self.assertIn("PKG_VERSION:=4.22.11", samba)
        self.assertIn("d569b298a81cc212a39e9d1813bc4ca5c71ac93c4ceb2eec03db178096958d00", samba)
        init = self.transmission.read_text(encoding="utf-8")
        self.assertLess(init.index("r619ac_require_storage"), init.index("config_file="))
        self.assertLess(init.index("r619ac_require_storage"), init.index("mkdir -p"))
        self.assertIn('r619ac_require_storage "$incomplete_dir"', init)
        self.assertIn('r619ac_require_storage "$watch_dir"', init)

    def test_unknown_upstream_version_is_rejected(self):
        original = self.samba.read_text(encoding="utf-8").replace("4.22.7", "4.22.8")
        self.samba.write_text(original, encoding="utf-8", newline="\n")
        self.assertNotEqual(self.prepare().returncode, 0)
        self.assertEqual(self.samba.read_text(encoding="utf-8"), original)

    def test_all_patches_are_checked_before_changing_sources(self):
        original = self.samba.read_text(encoding="utf-8")
        self.transmission.write_text("# 不匹配的上游初始化脚本\n", encoding="utf-8", newline="\n")
        self.assertNotEqual(self.prepare().returncode, 0)
        self.assertEqual(self.samba.read_text(encoding="utf-8"), original)


if __name__ == "__main__":
    unittest.main()
