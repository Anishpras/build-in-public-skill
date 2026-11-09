"""Tests for skills/build-in-public/scripts/ledger.py.

Run from the repo root:  python3 -m unittest discover -s tests -v
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest

SCRIPT = os.path.join(os.path.dirname(__file__), "..", "skills", "build-in-public", "scripts", "ledger.py")


class LedgerTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = self.tmp.name
        self.run_ok("init", "--project", "Acme")
        self.ledger = os.path.join(self.dir, "build-in-public", "ledger.json")

    def tearDown(self):
        self.tmp.cleanup()

    def run_cli(self, *args):
        return subprocess.run([sys.executable, SCRIPT, *args], cwd=self.dir, capture_output=True, text=True)

    def run_ok(self, *args):
        result = self.run_cli(*args)
        self.assertEqual(result.returncode, 0, msg=result.stderr + result.stdout)
        return result.stdout

    def data(self):
        with open(self.ledger, encoding="utf-8") as handle:
            return json.load(handle)

    def write(self, name, text):
        path = os.path.join(self.dir, name)
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(text)
        return path

    def new_episode(self, title="First deploy"):
        self.run_ok("new-episode", "--title", title, "--pillar", "build-log", "--since-commit", "abc1234")

    def test_init_creates_ledger_context_and_refuses_overwrite(self):
        self.assertTrue(os.path.exists(self.ledger))
        context = os.path.join(self.dir, "build-in-public", "context.md")
        with open(context, encoding="utf-8") as handle:
            self.assertIn("# Acme: Build-in-Public Context", handle.read())
        self.assertNotEqual(self.run_cli("init").returncode, 0)

    def test_episode_and_post_ids(self):
        self.new_episode()
        self.assertTrue(os.path.isdir(os.path.join(self.dir, "build-in-public", "episodes", "001-first-deploy")))
        draft = self.write("x.md", "Shipped it.\n---\nLink: example.com\n")
        self.run_ok("add-post", "--episode", "1", "--platform", "x", "--format", "thread", "--file", draft)
        self.run_ok("add-post", "--episode", "1", "--platform", "x", "--format", "post", "--file", draft)
        self.run_ok("add-post", "--episode", "1", "--platform", "linkedin", "--format", "post", "--file", draft)
        ids = [p["id"] for p in self.data()["posts"]]
        self.assertEqual(ids, ["E001-X1", "E001-X2", "E001-LI1"])
        self.assertEqual(self.data()["posts"][0]["hook"], "Shipped it.")

    def test_add_post_to_missing_episode_fails(self):
        draft = self.write("x.md", "hello")
        self.assertNotEqual(self.run_cli("add-post", "--episode", "4", "--platform", "x", "--format", "post", "--file", draft).returncode, 0)

    def test_posting_lifecycle_and_status(self):
        self.new_episode()
        draft = self.write("x.md", "Shipped it.")
        self.run_ok("add-post", "--episode", "1", "--platform", "x", "--format", "post", "--file", draft)
        self.run_ok("mark-posted", "e001-x1", "--url", "https://x.com/u/status/1")
        self.assertNotEqual(self.run_cli("mark-posted", "E001-X1").returncode, 0)  # already posted
        self.assertNotEqual(self.run_cli("mark-skipped", "E001-X1").returncode, 0)  # cannot skip a posted one
        self.run_ok("metrics", "E001-X1", "--impressions", "500", "--replies", "7")
        post = self.data()["posts"][0]
        self.assertEqual(post["status"], "posted")
        self.assertEqual(post["metrics"][0]["replies"], 7)
        status = self.run_ok("status")
        self.assertIn("this week 1/7", status)
        self.assertIn("done", self.run_ok("episodes"))

    def test_set_targets(self):
        self.run_ok("set-targets", "--x", "5", "--linkedin", "2")
        self.assertEqual(self.data()["settings"]["weekly_targets"], {"x": 5, "linkedin": 2})
        self.assertIn("this week 0/5", self.run_ok("status"))

    def test_next_reports_since_commit(self):
        self.new_episode()
        out = self.run_ok("next")
        self.assertIn("next episode: 002", out)
        self.assertIn("git log --oneline abc1234..HEAD", out)

    def test_x_check_counts_links_as_23_and_flags_problems(self):
        draft = self.write("x.md", "a" * 250 + " https://example.com/a/very/long/path/that/is/long #one #two\n")
        out = self.run_ok("check", draft, "--platform", "x")
        self.assertIn("post: 284/280", out)  # 250 + 1 space + 23 for the link + 10 for " #one #two"
        self.assertIn("post is 4 over the 280 limit", out)
        self.assertIn("link in the main post", out)
        self.assertIn("2 hashtags", out)

    def test_lint_catches_ai_tells_with_curly_apostrophes(self):
        draft = self.write("li.md", "It’s not a tool, it’s a system — really. Comment YES below and I'll DM you.\n")
        out = self.run_ok("check", draft, "--platform", "linkedin")
        self.assertIn("'it's not X, it's Y' reveal", out)
        self.assertIn("em dash", out)
        self.assertIn("engagement bait", out)

    def test_no_ledger_found(self):
        with tempfile.TemporaryDirectory() as empty:
            result = subprocess.run([sys.executable, SCRIPT, "status"], cwd=empty, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("ledger.py init", result.stderr)


if __name__ == "__main__":
    unittest.main()
