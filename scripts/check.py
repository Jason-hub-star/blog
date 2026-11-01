"""프로젝트 게이트: 0 통과 / 1 실패 / 2 도구 부재·시간 초과로 판정 못 함."""
import importlib.util
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    if not shutil.which("node") or importlib.util.find_spec("PIL") is None:
        print("판정 못 함: Node.js와 Pillow가 필요합니다. setup.py 및 Node.js 설치를 확인하세요.")
        return 2
    commands = [
        [sys.executable, "scripts/self_check.py"],
        [sys.executable, "tests/new_job.test.py"],
        ["node", "--check", "automation/browser_helpers.mjs"],
        ["node", "tests/browser_helpers.test.mjs"],
    ]
    for command in commands:
        try:
            result = subprocess.run(command, cwd=ROOT, timeout=120, check=False)
        except (OSError, subprocess.TimeoutExpired) as error:
            print("판정 못 함:", error)
            return 2
        if result.returncode:
            print("FAIL:", " ".join(command))
            return 1
    print("PASS: project gate")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
