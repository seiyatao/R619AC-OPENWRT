import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest

from test_build_checks import BASH, REPO


FEEDS = {"packages", "luci", "routing", "telephony", "video",
         "passwall_luci", "passwall_packages"}
GIT = shutil.which("git")


class SourcePolicyTest(unittest.TestCase):
    def test_all_feeds_are_locked(self):
        entries = [line.split() for line in (REPO / "feeds.conf.default").read_text(
            encoding="utf-8").splitlines() if line and not line.startswith("#")]
        self.assertEqual({entry[1] for entry in entries}, FEEDS)
        self.assertEqual(len(entries), len(FEEDS))
        for kind, name, source in entries:
            with self.subTest(feed=name):
                self.assertEqual(kind, "src-git")
                self.assertRegex(source, r"^https://[^\s;^]+\^[0-9a-f]{40}$")
        names = [entry[1] for entry in entries]
        self.assertLess(names.index("passwall_packages"), names.index("packages"))

    def test_workflow_pins_core_and_checks_sources(self):
        workflow = (REPO / ".github/workflows/build-openwrt.yml").read_text(encoding="utf-8")
        self.assertIn("REPO_BRANCH: openwrt-25.12", workflow)
        self.assertIn("REPO_COMMIT: d4cb7022585390564196f9849b2f5d10aba006e9", workflow)
        self.assertIn('checkout --detach "$REPO_COMMIT"', workflow)
        self.assertIn('scripts/check-build.sh" sources', workflow)
        self.assertIn("- 'feeds.conf.default'", workflow)
        self.assertNotIn("release_tag=25.12.6-test_", workflow)
        self.assertIsNotNone(re.search(r"^  REPO_COMMIT: [0-9a-f]{40}$", workflow, re.M))


@unittest.skipUnless(BASH and GIT, "需要 Bash 和 Git")
class SourceChecksTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="r619ac-sources-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.build_repo = self.root / "build-repo"
        (self.build_repo / "scripts").mkdir(parents=True)
        self.script = self.build_repo / "scripts/check-build.sh"
        shutil.copyfile(REPO / "scripts/check-build.sh", self.script)
        self.work = self.root / "openwrt"
        self.work.mkdir()
        self.git(self.work, "init", "--quiet")
        self.commit(self.work)
        self.revision = self.git(self.work, "rev-parse", "HEAD").stdout.strip()
        self.entries = [f"src-git {name} https://example.invalid/{name}.git^{self.revision}"
                        for name in sorted(FEEDS)]
        self.write_locks(self.entries)
        for name in FEEDS:
            self.git(self.root, "clone", "--quiet", "--shared", str(self.work),
                     str(self.work / "feeds" / name))

    def git(self, root, *args):
        return subprocess.run([GIT, "-C", str(root), *args], check=True,
                              capture_output=True, encoding="utf-8", timeout=20)

    def commit(self, root):
        self.git(root, "-c", "user.name=测试", "-c", "user.email=test@example.invalid",
                 "-c", "commit.gpgsign=false", "commit", "--quiet", "--allow-empty", "-m", "测试提交")

    def write_locks(self, entries):
        content = "\n".join(entries) + "\n"
        for path in (self.build_repo / "feeds.conf.default", self.work / "feeds.conf.default"):
            path.write_text(content, encoding="utf-8", newline="\n")

    def run_check(self, revision=None):
        env = os.environ.copy()
        env["REPO_COMMIT"] = self.revision if revision is None else revision
        return subprocess.run([BASH, self.script.as_posix(), "sources"], cwd=self.work,
                              env=env, capture_output=True, encoding="utf-8",
                              errors="replace", timeout=30)

    def test_expected_revisions_pass(self):
        result = self.run_check()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_wrong_core_revision_is_rejected(self):
        self.assertNotEqual(self.run_check("0" * 40).returncode, 0)

    def test_missing_core_revision_is_rejected(self):
        self.assertNotEqual(self.run_check("").returncode, 0)

    def test_floating_feed_is_rejected(self):
        self.entries[0] = self.entries[0].replace("^" + self.revision, ";openwrt-25.12")
        self.write_locks(self.entries)
        result = self.run_check()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("未固定完整提交", result.stderr)

    def test_missing_feed_is_rejected(self):
        self.write_locks(self.entries[:-1])
        self.assertNotEqual(self.run_check().returncode, 0)

    def test_empty_feed_list_is_rejected(self):
        self.write_locks([])
        result = self.run_check()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("固定 feed 清单不完整", result.stderr)

    def test_duplicate_feed_is_rejected(self):
        self.write_locks(self.entries + [self.entries[0]])
        result = self.run_check()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("重复的 feed", result.stderr)

    def test_changed_working_feed_list_is_rejected(self):
        (self.work / "feeds.conf.default").write_text("", encoding="utf-8")
        self.assertNotEqual(self.run_check().returncode, 0)

    def test_wrong_feed_revision_is_rejected(self):
        self.commit(self.work / "feeds/luci")
        result = self.run_check()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("feed 源码偏离固定提交", result.stderr)

    def test_parent_repository_is_not_accepted_as_feed(self):
        shutil.rmtree(self.work / "feeds/luci/.git")
        result = self.run_check()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("未检出为独立 Git 仓库", result.stderr)


if __name__ == "__main__":
    unittest.main()
