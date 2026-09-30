import os, subprocess, sys, tempfile, unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from tally import tally, parse, CHECKS  # noqa: E402

def run(fired="none", na="none", gate="CLEAR", body="findings text\n"):
    return f"{body}FIRED: {fired}\nNA: {na}\nGATE0: {gate}\n"

class TallyTest(unittest.TestCase):
    def test_majority_fires(self):
        r = tally([run("M1,O2"), run("M1"), run("M1,O2")])
        self.assertEqual(r["findings"], ["M1", "O2"])
        self.assertEqual(r["unstable"], [])

    def test_single_vote_is_unstable_not_a_finding(self):
        r = tally([run("H4"), run(), run()])
        self.assertEqual(r["findings"], [])
        self.assertEqual(r["unstable"], [("H4", 1)])

    def test_canonical_order(self):
        r = tally([run("X2,M1,C1")] * 3)
        self.assertEqual(r["findings"], ["M1", "C1", "X2"])

    def test_lowercase_and_spaces(self):
        r = tally([run(" m1 , o2 ")] * 3)
        self.assertEqual(r["findings"], ["M1", "O2"])

    def test_na_needs_majority(self):
        r = tally([run("O1"), run("O1"), run(na="O1")])
        self.assertEqual(r["findings"], ["O1"])
        self.assertEqual(r["na"], [])

    def test_na_majority_wins_and_is_not_unstable(self):
        r = tally([run("O1"), run(na="O1"), run(na="O1")])
        self.assertEqual(r["na"], ["O1"])
        self.assertEqual(r["findings"], [])
        self.assertEqual(r["unstable"], [])

    def test_gate_blocks_if_any_run_blocks(self):
        r = tally([run(gate="BLOCKED"), run(), run()])
        self.assertEqual(r["gate_blocked_runs"], 1)

    def test_missing_fired_line_is_an_error(self):
        with self.assertRaises(ValueError):
            parse("the grader ran out of turns here")

    def test_unknown_check_id_is_an_error(self):
        with self.assertRaises(ValueError):
            parse(run("M9"))

    def test_bad_gate_value_is_an_error(self):
        with self.assertRaises(ValueError):
            parse(run(gate="MAYBE"))

    def test_last_marker_lines_win(self):
        text = "FIRED: M1\nquoted from the draft\n" + run("O2")
        self.assertEqual(parse(text)["fired"], {"O2"})

    def test_twenty_five_checks(self):
        self.assertEqual(len(CHECKS), 25)

    def test_cli_output(self):
        with tempfile.TemporaryDirectory() as d:
            paths = []
            for i, t in enumerate([run("M1,H4", gate="BLOCKED"), run("M1"), run("M1", na="O1,O3,O4,C3")]):
                p = os.path.join(d, f"run{i}.md"); open(p, "w").write(t); paths.append(p)
            out = subprocess.run([sys.executable, os.path.join(os.path.dirname(__file__), "..", "scripts", "tally.py"), *paths],
                                 capture_output=True, text=True, check=True).stdout
        self.assertEqual(out, "FINDINGS: M1\nUNSTABLE: H4 (1/3)\nNOT-APPLICABLE: none\nGATE0: BLOCKED (1/3 runs)\n")

    def test_cli_names_the_bad_file(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "broken.md"); open(p, "w").write("no marker lines")
            res = subprocess.run([sys.executable, os.path.join(os.path.dirname(__file__), "..", "scripts", "tally.py"), p],
                                 capture_output=True, text=True)
        self.assertEqual(res.returncode, 1)
        self.assertIn("broken.md", res.stderr)

if __name__ == "__main__":
    unittest.main()
