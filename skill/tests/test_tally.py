import os, subprocess, sys, tempfile, unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from tally import tally, parse, CHECKS  # noqa: E402

TALLY = os.path.join(os.path.dirname(__file__), "..", "scripts", "tally.py")

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

    def test_even_run_count_needs_strict_majority(self):
        r = tally([run("M1"), run()])
        self.assertEqual(r["findings"], [])
        self.assertEqual(r["unstable"], [("M1", 1)])
        self.assertEqual(tally([run("M1"), run("M1")])["findings"], ["M1"])

    def test_single_run_is_its_own_majority(self):
        self.assertEqual(tally([run("H1")])["findings"], ["H1"])

    def test_unanimous_na_is_neither_finding_nor_unstable(self):
        r = tally([run(na="C3")] * 3)
        self.assertEqual((r["findings"], r["unstable"], r["na"]), ([], [], ["C3"]))

    def test_fired_and_na_in_one_run_resolve_by_majority(self):
        r = tally([run("O3", na="O3"), run("O3"), run()])
        self.assertEqual(r["findings"], ["O3"])
        self.assertEqual(r["na"], [])

    def test_duplicate_id_in_a_run_counts_once(self):
        r = tally([run("M1,M1,m1"), run(), run()])
        self.assertEqual(r["unstable"], [("M1", 1)])

    def test_none_is_case_insensitive_and_empty_is_none(self):
        self.assertEqual(parse(run(fired="None", na=""))["fired"], set())
        self.assertEqual(parse(run(fired="NONE"))["na"], set())

    def test_gate_value_is_case_insensitive(self):
        self.assertTrue(parse(run(gate="blocked"))["blocked"])
        self.assertFalse(parse(run(gate=" clear "))["blocked"])

    def test_crlf_line_endings(self):
        text = run("M1,O2", gate="BLOCKED").replace("\n", "\r\n")
        p = parse(text)
        self.assertEqual((p["fired"], p["blocked"]), ({"M1", "O2"}, True))

    def test_every_gate_block_is_counted(self):
        r = tally([run(gate="BLOCKED")] * 3)
        self.assertEqual(r["gate_blocked_runs"], 3)

    def test_markdown_decorated_markers_are_an_error(self):
        with self.assertRaises(ValueError):
            parse("**FIRED:** M1\n**NA:** none\n**GATE0:** CLEAR\n")

    def test_indented_markers_are_an_error(self):
        with self.assertRaises(ValueError):
            parse("  FIRED: M1\n  NA: none\n  GATE0: CLEAR\n")

    def test_trailing_commentary_on_a_marker_is_an_error(self):
        with self.assertRaises(ValueError):
            parse(run("M1 (see above)"))

    def test_each_marker_is_required(self):
        for missing in ("FIRED", "NA", "GATE0"):
            text = "".join(l + "\n" for l in run().splitlines() if not l.startswith(missing + ":"))
            with self.subTest(missing=missing), self.assertRaises(ValueError):
                parse(text)

    def test_empty_gate_is_an_error(self):
        with self.assertRaises(ValueError):
            parse(run(gate=""))

    def test_unknown_na_id_is_an_error(self):
        with self.assertRaises(ValueError):
            parse(run(na="Z1"))

    def test_cli_no_files_is_an_error(self):
        res = subprocess.run([sys.executable, TALLY], capture_output=True, text=True)
        self.assertEqual(res.returncode, 1)
        self.assertEqual(res.stdout, "")

    def test_cli_missing_file_is_an_error(self):
        res = subprocess.run([sys.executable, TALLY, "/nonexistent/run1.md"], capture_output=True, text=True)
        self.assertEqual(res.returncode, 1)
        self.assertIn("run1.md", res.stderr)

    def test_cli_one_broken_run_fails_the_whole_tally(self):
        with tempfile.TemporaryDirectory() as d:
            paths = []
            for i, t in enumerate([run("M1"), run("M1"), "ran out of turns"]):
                p = os.path.join(d, f"run{i}.md"); open(p, "w").write(t); paths.append(p)
            res = subprocess.run([sys.executable, TALLY, *paths], capture_output=True, text=True)
        self.assertEqual(res.returncode, 1)
        self.assertEqual(res.stdout, "")
        self.assertIn("run2.md", res.stderr)

    def test_cli_non_utf8_file_is_an_error(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "bin.md"); open(p, "wb").write(b"\xff\xfe\x00FIRED")
            res = subprocess.run([sys.executable, TALLY, p], capture_output=True, text=True,
                                 env={**os.environ, "PYTHONUTF8": "1"})
        self.assertEqual(res.returncode, 1)

    def test_cli_na_and_unstable_formatting(self):
        with tempfile.TemporaryDirectory() as d:
            paths = []
            for i, t in enumerate([run("H4,V1", na="C3"), run(na="C3"), run("V1", na="C3")]):
                p = os.path.join(d, f"run{i}.md"); open(p, "w").write(t); paths.append(p)
            out = subprocess.run([sys.executable, TALLY, *paths], capture_output=True, text=True, check=True).stdout
        self.assertEqual(out, "FINDINGS: V1\nUNSTABLE: H4 (1/3)\nNOT-APPLICABLE: C3\nGATE0: CLEAR (0/3 runs)\n")


if __name__ == "__main__":
    unittest.main()
