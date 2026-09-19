from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class NoGitHubActions(unittest.TestCase):
    def test_no_github_actions_workflows(self):
        workflow_root = ROOT / ".github" / "workflows"
        files = sorted(
            path.relative_to(ROOT).as_posix()
            for path in workflow_root.rglob("*")
            if path.is_file()
        ) if workflow_root.exists() else []
        self.assertEqual(
            files,
            [],
            "GitHub Actions is forbidden for this repository; remove .github/workflows files.",
        )


if __name__ == "__main__":
    unittest.main()
