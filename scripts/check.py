"""공개 가상 입력 검사: 0 통과 / 1 실패 / 2 필수 도구 미설치."""
import importlib.util
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    if importlib.util.find_spec("PIL") is None or not all(shutil.which(t) for t in ["node", "ffmpeg"]):
        print("판정 못 함: setup.py로 Pillow를 설치하고 Node.js·FFmpeg를 PATH에서 확인하세요.")
        return 2
    for command in [
        [sys.executable, "scripts/self_check.py"],
        ["node", "--check", "automation/browser_helpers.mjs"],
        ["node", "--check", "automation/verify_editor.mjs"],
        ["node", "tests/editor_verifier.test.mjs"],
    ]:
        try:
            result = subprocess.run(command, cwd=ROOT, timeout=120)
        except (OSError, subprocess.TimeoutExpired) as error:
            print("판정 못 함:", error)
            return 2
        if result.returncode:
            return 1
    print("PASS: 금강이지스 portable gate. 실제 네이버 저장복원은 별도입니다.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
