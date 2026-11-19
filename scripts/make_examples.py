"""Run every stand and save example reports to examples/<stand>/.

Usage:  python scripts/make_examples.py [--duration 60] [--idle-timeout 0.5]
Needs Docker (with 'docker compose') and the package installed
(pip install -e .). Works the same on Windows, macOS and Linux.
"""
import argparse
import contextlib
import json
import subprocess
import sys
import time
from pathlib import Path

from docker_net_profiler.reporters.console_reporter import print_report
from docker_net_profiler.reporters.html_reporter import save_html_report
from docker_net_profiler.reporters.markdown_reporter import save_markdown_report

ROOT = Path(__file__).resolve().parent.parent

def run(cmd, **kwargs):
    print("+", " ".join(map(str, cmd)))
    return subprocess.run(cmd, check=True, **kwargs)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--duration", type=int, default=60)
    parser.add_argument("--idle-timeout", type=float, default=0.5)
    parser.add_argument("--interval", type=int, default=5)
    args = parser.parse_args()

    for stand in sorted((ROOT / "stands").iterdir()):
        compose = stand / "docker-compose.yml"
        if not compose.exists():
            continue

        out_dir = ROOT / "examples" / stand.name
        out_dir.mkdir(parents=True, exist_ok=True)
        prefix = "s" + stand.name[5] + "-"  # stand1-... -> "s1-"

        run(["docker", "compose", "-f", str(compose), "up", "-d"])
        try:
            time.sleep(5)  # let containers start
            json_path = out_dir / "report.json"
            run([
                sys.executable, "-m", "docker_net_profiler",
                "--name-filter", prefix,
                "--interval", str(args.interval),
                "--duration", str(args.duration),
                "--idle-timeout", str(args.idle_timeout),
                "--format", "json", "--output", str(json_path),
            ])
            # One observation run, all formats rendered from its result.
            results = json.loads(
                json_path.read_text(encoding="utf-8"))["containers"]
            save_markdown_report(results, str(out_dir / "report.md"))
            save_html_report(results, str(out_dir / "report.html"))
            with open(out_dir / "report.txt", "w", encoding="utf-8") as f:
                with contextlib.redirect_stdout(f):
                    print_report(results)
        finally:
            run(["docker", "compose", "-f", str(compose), "down"])


if __name__ == "__main__":
    main()
