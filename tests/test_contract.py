"""Cross-file contracts: the rubric, the tally, the agents, the guards and the
fixtures must agree with each other. Each piece has its own unit tests; these
catch the drift between them."""
import glob, json, os, re, subprocess, sys, tempfile, unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL = os.path.join(REPO, "skill")
sys.path.insert(0, os.path.join(SKILL, "scripts"))
from tally import CHECKS, parse, tally  # noqa: E402


def read(*parts):
    with open(os.path.join(REPO, *parts)) as f:
        return f.read()


def frontmatter(text):
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    assert m, "no frontmatter"
    return m.group(1)


def hook(path, stdin_obj, home):
    guard = os.path.join(SKILL, "scripts", path)
    res = subprocess.run(["bash", guard], input=json.dumps(stdin_obj), text=True,
                         capture_output=True, env={**os.environ, "HOME": home})
    return res.returncode


class RubricTest(unittest.TestCase):
    def test_checks_md_defines_exactly_the_tallied_ids_in_order(self):
        ids = re.findall(r"^### ([A-Z]\d) — ", read("skill", "references", "checks.md"), re.M)
        self.assertEqual(ids, CHECKS)

    def test_checks_md_defines_gate_0(self):
        self.assertRegex(read("skill", "references", "checks.md"), r"(?m)^## Gate 0")

    def test_canon_routes_every_check_but_the_compliance_pair(self):
        canon = read("skill", "references", "canon.md")
        routed = set()
        for line in re.findall(r"^Enforced by: (.*)\.$", canon, re.M):
            for item in line.split(","):
                item = item.strip()
                if item != "Gate 0":
                    self.assertIn(item, CHECKS, f"canon routes unknown check {item}")
                    routed.add(item)
        self.assertEqual(set(CHECKS) - routed, {"X1", "X2"})
        self.assertIn("deliberately unrouted", canon)

    def test_canon_has_ten_numbered_sections(self):
        nums = re.findall(r"^## (\d+)\. ", read("skill", "references", "canon.md"), re.M)
        self.assertEqual(nums, [str(i) for i in range(1, 11)])


class AgentTest(unittest.TestCase):
    def test_grader_is_cold(self):
        fm = frontmatter(read("agents", "copy-grader.md"))
        self.assertRegex(fm, r"(?m)^name: copy-grader$")
        self.assertRegex(fm, r"(?m)^tools: Read$")
        self.assertRegex(fm, r"(?m)^omitClaudeMd: true$")
        self.assertRegex(fm, r'matcher: "Read"')

    def test_source_checker_is_fenced(self):
        fm = frontmatter(read("agents", "copy-source-checker.md"))
        self.assertRegex(fm, r"(?m)^name: copy-source-checker$")
        self.assertRegex(fm, r"(?m)^tools: Bash, WebFetch$")
        self.assertRegex(fm, r"(?m)^omitClaudeMd: true$")
        self.assertRegex(fm, r'matcher: "Bash"')

    def test_hook_commands_point_at_executable_guards_in_the_skill(self):
        for agent, script in (("copy-grader.md", "grader-read-guard.sh"),
                              ("copy-source-checker.md", "source-check-guard.sh")):
            cmd = re.search(r'command: "(.*)"', frontmatter(read("agents", agent))).group(1)
            self.assertEqual(cmd, f"$HOME/.claude/skills/copy-chief/scripts/{script}")
            self.assertTrue(os.access(os.path.join(SKILL, "scripts", script), os.X_OK), script)

    def test_grader_reads_exactly_what_the_guard_admits(self):
        body = read("agents", "copy-grader.md")
        listed = re.findall(r"^- (~/\.claude/skills/copy-chief/\S+)$", body, re.M)
        self.assertEqual(sorted(os.path.basename(p) for p in listed), ["ai-tells.md", "checks.md"])
        with tempfile.TemporaryDirectory() as home:
            os.makedirs(os.path.join(home, ".claude", "skills"))
            os.symlink(SKILL, os.path.join(home, ".claude", "skills", "copy-chief"))
            for p in listed:
                self.assertEqual(hook("grader-read-guard.sh", {"tool_input": {"file_path": p}}, home), 0, p)
            for other in ("references/canon.md", "fixtures/planted-key.md", "SKILL.md"):
                p = "~/.claude/skills/copy-chief/" + other
                self.assertEqual(hook("grader-read-guard.sh", {"tool_input": {"file_path": p}}, home), 2, p)

    def test_grader_output_contract_is_what_tally_parses(self):
        body = read("agents", "copy-grader.md")
        for marker in ("FIRED:", "NA:", "GATE0:"):
            self.assertRegex(body, rf"(?m)^{marker} ")
        self.assertIn("GATE0: BLOCKED or CLEAR", body)

    def test_source_checker_templates_pass_its_own_guard(self):
        body = read("agents", "copy-source-checker.md")
        templates = re.findall(r"`(curl [^`]+)`", body)
        self.assertGreaterEqual(len(templates), 4)
        fill = {"<PMID>": "11693190", "<id>": "2401.00001", "<YYYY-MM-DD>": "2026-01-01",
                "<n>": "21", "<part>": "101", "<section>": "101.93"}
        for t in templates:
            for k, v in fill.items():
                t = t.replace(k, v)
            if "http" not in t:
                t += ' "https://example.com/page"'
            self.assertNotIn("<", t, t)
            code = hook("source-check-guard.sh", {"tool_input": {"command": t}}, os.environ["HOME"])
            self.assertEqual(code, 0, t)


class SkillTest(unittest.TestCase):
    def test_frontmatter(self):
        fm = frontmatter(read("skill", "SKILL.md"))
        self.assertRegex(fm, r"(?m)^name: copy-chief$")
        self.assertRegex(fm, r"(?m)^description: Use when ")

    def test_every_path_the_skill_names_exists(self):
        text = read("skill", "SKILL.md")
        paths = set(re.findall(r"`((?:references|scripts|fixtures)/[\w./-]+)`", text))
        paths |= {m for m in re.findall(r"~/\.claude/skills/copy-chief/([\w./-]+)", text)}
        self.assertTrue(paths)
        for p in paths:
            self.assertTrue(os.path.exists(os.path.join(SKILL, p)), p)

    def test_every_agent_the_skill_dispatches_exists(self):
        text = read("skill", "SKILL.md")
        for agent in set(re.findall(r"`(copy-[a-z-]+)`", text)) - {"copy-chief"}:
            self.assertTrue(os.path.exists(os.path.join(REPO, "agents", agent + ".md")), agent)


class FixtureTest(unittest.TestCase):
    def test_planted_key_plants_one_defect_per_check(self):
        rows = re.findall(r"^\| ([A-Z]\d) \|", read("skill", "fixtures", "planted-key.md"), re.M)
        self.assertEqual(rows, CHECKS)

    def test_pairs_key_targets_real_checks_and_files(self):
        key = read("skill", "fixtures", "pairs", "key.md")
        rows = re.findall(r"^\| (\S+\.md) \| (\S+) \|", key, re.M)
        self.assertEqual(len(rows), 7)
        for name, target in rows:
            self.assertTrue(os.path.exists(os.path.join(SKILL, "fixtures", "pairs", name)), name)
            if target != "none":
                self.assertIn(target, CHECKS)
                self.assertEqual(name, target + ".md")

    def test_every_recorded_grader_run_parses(self):
        runs = glob.glob(os.path.join(SKILL, "fixtures", "pairs", "runs", "*", "run*.md"))
        self.assertEqual(len(runs), 21)
        for r in runs:
            with open(r) as f:
                parse(f.read())

    def test_recorded_results_match_a_fresh_tally(self):
        results = read("skill", "fixtures", "pairs", "results-2026-09-26.md")
        blocks = re.findall(r"^## (\w+)\.md\n```\n(.*?)```", results, re.M | re.S)
        self.assertEqual(len(blocks), 7)
        tally_py = os.path.join(SKILL, "scripts", "tally.py")
        for name, recorded in blocks:
            runs = sorted(glob.glob(os.path.join(SKILL, "fixtures", "pairs", "runs", name, "run*.md")))
            self.assertEqual(len(runs), 3, name)
            out = subprocess.run([sys.executable, tally_py, *runs], capture_output=True, text=True, check=True).stdout
            self.assertEqual(out, recorded, name)


if __name__ == "__main__":
    unittest.main()
