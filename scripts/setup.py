"""Mac/Windows 공통 첫 실행. 개인 설정은 이미 있으면 보존한다."""
from pathlib import Path
import os
import shutil
import subprocess
import sys
import venv

ROOT = Path(__file__).resolve().parents[1]


def main():
    if sys.version_info < (3, 10):
        raise SystemExit("Python 3.10 이상이 필요합니다")
    python = ROOT / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    if not python.exists():
        venv.EnvBuilder(with_pip=True).create(ROOT / ".venv")
    subprocess.run([str(python), "-m", "pip", "install", "-r", str(ROOT / "requirements.txt")], check=True)
    local = ROOT / "post.local.json"
    if not local.exists():
        shutil.copy2(ROOT / "post.example.json", local)
    (ROOT / "data/photos").mkdir(parents=True, exist_ok=True)
    subprocess.run([str(python), str(ROOT / "scripts/self_check.py")], check=True)
    print("Ready. docs/아내_시작하기.md를 열고 scripts/new_job.py로 새 현장 폴더를 만드세요.")
    print("Build:", str(python), "automation/build_assets.py --config <현장폴더>/post.local.json")


if __name__ == "__main__":
    main()
