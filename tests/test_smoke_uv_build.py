import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


class TestSmokeUvBuild(unittest.TestCase):
    def test_uv_build_consumer_project(self):
        if shutil.which("uv") is None or shutil.which("git") is None:
            self.skipTest("uv and git are required for this smoke test")

        plugin_root = Path(__file__).resolve().parents[1]
        plugin_req = f"hatch-mpt-versioning @ {plugin_root.as_uri()}"

        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "consumer"
            root.mkdir(parents=True, exist_ok=True)

            # Minimal hatchling project
            (root / "src" / "consumer_pkg").mkdir(parents=True, exist_ok=True)
            (root / "src" / "consumer_pkg" / "__init__.py").write_text("", encoding="utf-8")

            (root / "pyproject.toml").write_text(
                "\n".join(
                    [
                        "[build-system]",
                        'requires = ["hatchling>=1.21.0", "' + plugin_req + '"]',
                        'build-backend = "hatchling.build"',
                        "",
                        "[project]",
                        'name = "consumer-pkg"',
                        'dynamic = ["version"]',
                        'requires-python = ">=3.10"',
                        "",
                        "[tool.hatch.version]",
                        'source = "mpt-git-describe"',
                        "",
                        "[tool.hatch.build.targets.wheel]",
                        'packages = ["src/consumer_pkg"]',
                        "",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            def run(cmd):
                return subprocess.run(cmd, cwd=root, check=True, capture_output=True, text=True)

            # Create a minimal git repository with a tag and one commit ahead.
            # (This is required for git-describe based versioning.)
            try:
                run(["git", "init"])
            except subprocess.CalledProcessError as e:
                # Some sandboxed environments forbid creating .git/hooks.
                if "Operation not permitted" in (e.stderr or ""):
                    self.skipTest("Sandbox forbids `git init` (cannot create .git/hooks)")
                raise

            run(["git", "config", "user.email", "test@example.com"])
            run(["git", "config", "user.name", "Test"])
            run(["git", "add", "."])
            run(["git", "commit", "-m", "init"])
            run(["git", "tag", "1.0.0"])

            (root / "src" / "consumer_pkg" / "__init__.py").write_text("x = 1\n", encoding="utf-8")
            run(["git", "add", "."])
            run(["git", "commit", "-m", "change"])

            sha = run(["git", "rev-parse", "--short=7", "HEAD"]).stdout.strip()
            expected_version = f"1.0.1+g{sha}"

            # Build and assert version is derived correctly.
            subprocess.run(["uv", "build"], cwd=root, check=True)

            dist_files = list((root / "dist").glob("*"))
            self.assertTrue(dist_files, "Expected dist artifacts to be created")

            names = "\n".join(p.name for p in dist_files)
            self.assertIn(expected_version, names)


if __name__ == "__main__":
    unittest.main()

