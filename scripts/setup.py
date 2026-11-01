"""금강이지스 Mac/Windows 실행 환경. 기존 현장 자료는 덮어쓰지 않는다."""
import os
from pathlib import Path
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
    job = ROOT / "현장작업/새_현장"
    for name in ["01_원본사진", "01_리뷰캡처", "02_제작물"]:
        (job / name).mkdir(parents=True, exist_ok=True)
    if not (job / "post.json").exists():
        shutil.copy2(ROOT / "post.example.json", job / "post.json")
    if not (job / "원본목록.json").exists():
        (job / "원본목록.json").write_text("[]\n", encoding="utf-8")
    print("준비 완료. docs/Windows_시작하기.md를 읽고 금강이지스 프로젝트 폴더를 여세요.")
    print("전체 검사에는 Node.js와 FFmpeg가 필요합니다:", str(python), "scripts/check.py")


if __name__ == "__main__":
    main()
