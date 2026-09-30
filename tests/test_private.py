"""Nothing private reaches the public repo. Generic leaks (a home directory
path) are checked everywhere. Named terms, such as client names, live in
.git/info/private-terms, one per line, which git never pushes; the check is
skipped where that file does not exist."""
import os, subprocess, unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TERMS = os.path.join(REPO, ".git", "info", "private-terms")


def tracked():
    out = subprocess.run(["git", "-C", REPO, "ls-files", "-z"], capture_output=True, text=True)
    if out.returncode != 0:
        raise unittest.SkipTest("not a git checkout")
    for name in filter(None, out.stdout.split("\0")):
        with open(os.path.join(REPO, name), "rb") as f:
            yield name, f.read().decode("utf-8", "replace")


class PrivateTest(unittest.TestCase):
    def test_no_home_directory_paths(self):
        for name, text in tracked():
            if name == "tests/test_private.py":
                continue
            for leak in ("/Users/", "/home/runner/"):
                self.assertFalse(leak in text, f"{name} contains {leak}")

    def test_no_private_terms(self):
        if not os.path.exists(TERMS):
            self.skipTest("no .git/info/private-terms")
        with open(TERMS) as f:
            terms = [t.strip().lower() for t in f if t.strip() and not t.startswith("#")]
        self.assertTrue(terms)
        for name, text in tracked():
            low = (name + "\n" + text).lower()
            for t in terms:
                self.assertFalse(t in low, f"{name} contains a private term")

    def test_private_fixtures_are_not_tracked(self):
        names = [n for n, _ in tracked()]
        self.assertFalse([n for n in names if "/held-out" in n or "/source-check/" in n])


if __name__ == "__main__":
    unittest.main()
